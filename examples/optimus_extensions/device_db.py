device_db.update({
    # influxdb for Optimus
    'optimus_influx_db': {
        'type': 'controller',
        'host': '::1',
        'port': 3278,
        'command': 'aqctl_influx_db -p {port} --bind {bind} '
                   '--db optimus_exp --server-db my-server.duckdns.org '
                   '--user-db oaf --password-db oaf_password '
    }
})
