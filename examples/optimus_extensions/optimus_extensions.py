"""
For some experiment, we need to add some sort of data logging to save the data to a database.
This snippet of code provides overrides for classes so that Optimus information can be saved
to an InfluxDB database.
"""

import dax.base.exceptions
from dax.scheduler import CalibrationJob, DaxScheduler, NodeAction, Policy
from artiq.experiment import Experiment

import time
import typing
from typing import Type


class OAFDaxScheduler(DaxScheduler):

    def build(self, *args: typing.Any, **kwargs: typing.Any) -> None:
        super(OAFDaxScheduler, self).build(*args, **kwargs)

        # Get the optimus influxdb device
        self._optimus_influx = self.get_device('optimus_influx_db')

    def wave(self, *, wave: float,
             root_nodes,
             root_action: NodeAction,
             policy: Policy,
             reverse: bool,
             priority: int,
             depth: int = -1,
             start_depth: int = 0) -> None:
        """Run a wave over the graph.

        :param wave: The wave identifier
        :param root_nodes: A collection of root nodes
        :param root_action: The root node action
        :param policy: The policy for this wave
        :param reverse: The reverse wave flag
        :param priority: Submit priority
        :param depth: Maximum recursion depth (:const:`-1` for infinite recursion depth)
        :param start_depth: Depth to start visiting nodes (:const:`0` to start at the root nodes)
        """
        assert isinstance(wave, float), 'Wave must be of type float'
        # assert isinstance(root_nodes, collections.abc.Collection), 'Root nodes must be a collection'
        # assert all(isinstance(j, Node) for j in root_nodes), 'All root nodes must be of type Node'
        assert isinstance(root_action, NodeAction), 'Root action must be of type NodeAction'
        assert isinstance(policy, Policy), 'Policy must be of type Policy'
        assert isinstance(reverse, bool), 'Reverse flag must be of type bool'
        assert isinstance(priority, int), 'Priority must be of type int'
        assert isinstance(depth, int), 'Depth must be of type int'
        assert isinstance(start_depth, int), 'Start depth must be of type int'

        # Select the correct graph for this wave
        graph = self._graph_reversed if reverse else self._graph
        # Set of submitted nodes in this wave
        submitted = set()

        def submit(node) -> None:
            """Submit a node.

            :param node: The node to submit
            """

            if node not in submitted:
                # Submit this node
                node.submit(wave=wave, priority=priority)
                submitted.add(node)

        def recurse(node, action: NodeAction, current_depth: int, current_start_depth: int) -> None:
            """Process nodes recursively.

            :param node: The current node to process
            :param action: The action provided by the previous node
            :param current_depth: Current remaining recursion depth
            :param current_start_depth: Current remaining start depth
            """

            if current_start_depth <= 0:
                # Visit the current node and get the new action based on the policy
                new_action: NodeAction = policy.action(action, node.visit(wave=wave))
                # See if the node is submittable
                submittable: bool = new_action.submittable()
            else:
                # Pass the provided action
                new_action = action
                # This node is not submittable
                submittable = False

            if submittable and reverse:
                # Submit this node before recursion
                submit(node)

            if current_depth != 0:
                # Recurse over successors
                for successor in graph.successors(node):
                    recurse(successor, new_action, current_depth - 1, current_start_depth - 1)

            if submittable and not reverse:
                # Submit this node after recursion
                submit(node)

        for root_node in root_nodes:
            # Recurse over all root nodes using the root action
            recurse(root_node, root_action, depth, start_depth)

        if submitted:
            # Log submitted nodes
            self.logger.debug(f'Submitted node(s): {", ".join(sorted(node.get_name() for node in submitted))}')

        # Save wave data to influxdb
        wave_data = [
            {
                'measurement': 'waves',
                'fields': {
                    'wave_id': wave,
                    'timed_trigger': depth == -1 and start_depth == 0,
                    'root_nodes': str([node.get_name() for node in root_nodes]),
                    'submitted_nodes': str([node.get_name() for node in submitted])
                }
            }
        ]

        self._optimus_influx.write_points(wave_data)


class OAFCalibrationJob(CalibrationJob):

    def build_job(self) -> None:
        self._optimus_influx = self.get_device('optimus_influx_db')

    @classmethod
    def meta_exp_factory(cls) -> Type[Experiment]:
        meta_exp = super().meta_exp_factory()

        class MetaExperiment(meta_exp):
            def run(self):
                try:
                    # check_state (only if diagnose flag is False and timeout is not None)
                    if not self.get_dataset(self._my_dataset_keys[cls.DIAGNOSE_FLAG_KEY], False, archive=False) \
                            and self._timeout is not None and self.check_state():
                        return

                    last_cal = self.get_dataset(self._my_dataset_keys[cls.LAST_CAL_KEY], 0.0, archive=False)
                    last_check = self.get_dataset(self._my_dataset_keys[cls.LAST_CHECK_KEY], 0.0, archive=False)
                    assert isinstance(last_cal, float), 'Unexpected return type from dataset'
                    assert isinstance(last_check, float), 'Unexpected return type from dataset'
                    last_cal_or_check: float = max(last_cal, last_check)

                    # Prep data for influx
                    wave_data = [
                        {
                            'measurement': 'node_results',
                            'tags': {
                                'node_name': cls.get_name()
                            },
                            'fields': {
                                'check_time': time.time(),
                                'check_result': 'None',
                                'calibration_result': 'None'
                            }
                        }
                    ]

                    # check_data
                    try:
                        if self._check_exception is not None:
                            raise self._check_exception
                        self._check_analyze = True
                        self._check_exp.run()
                    except dax.base.exceptions.BadDataError:
                        self.logger.info('Bad data, triggering diagnose wave')
                        for _, key_dict in self._dep_dataset_keys.items():
                            self.set_dataset(key_dict[cls.DIAGNOSE_FLAG_KEY], True,
                                             broadcast=True, persist=True, archive=False)
                        self._dax_scheduler.submit(cls.get_name(), policy=str(Policy.GREEDY), depth=1, start_depth=1,
                                                   priority=self._scheduler.priority + 1)
                        if cls.CORE_ATTR is not None and hasattr(self._check_exp, cls.CORE_ATTR):
                            getattr(self._check_exp, cls.CORE_ATTR).comm.close()  # Close communications before pausing
                        dax.util.artiq.pause_strict_priority(self._scheduler)
                        self.logger.info('Diagnose finished, continuing to calibration')
                        wave_data[0]['fields']['check_result'] = 'Fail'

                    except dax.base.exceptions.OutOfSpecError:
                        self.logger.info('Out of spec, continuing to calibration')
                        wave_data[0]['fields']['check_result'] = 'Fail'
                    else:
                        self.logger.info('Check data passed, returning')
                        wave_data[0]['fields']['check_result'] = 'Pass'
                        self._optimus_influx.write_points(wave_data)
                        self.set_dataset(self._my_dataset_keys[cls.LAST_CHECK_KEY], time.time(),
                                         broadcast=True, persist=True, archive=False)
                        return

                    # If made it this far, that means check_data failed and there will be a calibration. Prepare another
                    #   influx data point
                    wave_data = [
                        {
                            'measurement': 'node_results',
                            'tags': {
                                'node_name': cls.get_name()
                            },
                            'fields': {
                                'check_time': time.time(),
                                'check_result': 'None',
                                'calibration_result': 'None'
                            }
                        }
                    ]
                    # calibrate
                    try:
                        self._calibration_exp = self._cal_cls(self._cal_managers)
                        self._calibration_exp.prepare()
                        self._calibration_exp.run()
                    except dax.base.exceptions.FailedCalibrationError as fce:
                        self.logger.exception(fce)
                        # Write to influx
                        wave_data[0]['fields']['calibration_result'] = 'Fail'
                        self._optimus_influx.write_points(wave_data)
                        self.submit_barrier()
                    else:
                        self.logger.info('Calibration succeeded')
                        self._cal_analyze = True
                        # Write to influx
                        wave_data[0]['fields']['calibration_result'] = 'Pass'
                        self._optimus_influx.write_points(wave_data)
                        self.set_dataset(self._my_dataset_keys[cls.LAST_CAL_KEY], time.time(),
                                         broadcast=True, persist=True, archive=False)
                except Exception:
                    if cls.GREEDY_FAILURE:
                        self.logger.exception('Uncaught exception')
                        self.submit_barrier()
                    else:
                        raise
                finally:
                    self.set_dataset(self._my_dataset_keys[cls.DIAGNOSE_FLAG_KEY], False,
                                     broadcast=True, persist=True, archive=False)

            def analyze(self) -> None:

                self.logger.exception(f'My dataset value is {self.get_dataset_sys(self._LAST_SUBMIT_KEY, fallback=0)}')
                # make sure file names are unique in the case that the check class and cal class are the same
                file_name_gen = dax.util.output.FileNameGenerator(self._scheduler)
                check_name = file_name_gen(cls.CHECK_CLASS_NAME, 'h5')
                cal_name = file_name_gen(cls.CALIBRATION_CLASS_NAME, 'h5')
                if self._check_analyze:
                    try:
                        self._check_exp.analyze()
                    finally:
                        check_meta = {
                            'rid': self._scheduler.rid,
                            'arguments': sipyco.pyon.encode(self._check_args)
                        }
                        self._check_managers.write_hdf5(check_name, metadata=check_meta)
                if self._cal_analyze:
                    try:
                        self._calibration_exp.analyze()
                    finally:
                        cal_meta = {
                            'rid': self._scheduler.rid,
                            'arguments': sipyco.pyon.encode(self._cal_args)
                        }
                        self._cal_managers.write_hdf5(cal_name, metadata=cal_meta)

        return MetaExperiment
