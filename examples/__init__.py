import os
import sys

base_path = os.path.dirname(__file__)

sys.path.append(os.path.abspath(os.path.join(base_path, '..')))


from pykurento import KurentoClient

kurento = KurentoClient("ws://192.168.99.100:32781/kurento")

def render_view(handler, name):
  with open("%s/views/%s.html" % (base_path, name), "r") as f:
    handler.finish(f.read())
