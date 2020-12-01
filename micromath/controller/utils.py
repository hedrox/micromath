import requests
import time

from multiprocessing import Process


def initialize_kibana():
    """
    Creating a daemon process to initialize kibana with two index pattern so that they don't have to be
    manually added by the user when entering kibana for the first time.
    """
    def poll_kibana_index_pattern():
        """
        We are polling for 5 minutes for kibana to be up so that the requests and logging index 
        pattern can be created.
        Tasks such as this could be more scalable done using Celery.
        """

        indices = ["requests", "logging", "container_logs"]
        tries = 30
        while indices and tries > 0:
            for index in indices:
                payload = {"attributes": {"title": index, "timeFieldName": "@timestamp"}}
                try:
                    res = requests.post("http://kibana:5601/api/saved_objects/index-pattern/{}".format(index), json=payload, headers={"kbn-xsrf": "true"}, verify=False)
                    if res.status_code == 200:
                        indices.remove(index)
                    else:
                        time.sleep(10)
                        tries -= 1
                except Exception as e:
                    time.sleep(10)
                    tries -= 1
                    continue

    proc = Process(target=poll_kibana_index_pattern)
    proc.daemon = True
    proc.start()
