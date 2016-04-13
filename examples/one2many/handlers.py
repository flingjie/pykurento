# coding=utf8
import tornado.websocket
import tornado.web
import json
from examples import kurento, render_view
from pykurento import media

g_session_id = None
g_pipeline = None
g_incoming_end = None
g_candidates = {}
g_viewers = {}


class One2ManyHandler(tornado.web.RequestHandler):
     def get(self):
        render_view(self, "one2many")


class CallHandler(tornado.websocket.WebSocketHandler):
    def __init__(self, application, request, **kwargs):
        tornado.websocket.WebSocketHandler.__init__(self, application, request, **kwargs)

    def open(self, *args, **kwargs):
        print('open ...')

    def on_message(self, message):
        data = json.loads(message)
        action = data.get('id')
        if action == u'viewer':
            self.viewer(data.get("sdpOffer"))
        elif action == u'presenter':
            self.stop()
            self.presenter(data.get("sdpOffer"))
        elif action == u'onIceCandidate':
            self.on_ice_candidate(data.get("candidate"))
        elif action == 'stop':
            self.stop()

    def on_close(self):
        print('close ...')

    def check_origin(self, origin):
        return True

    def viewer(self, sdp_offer):
        global g_session_id, g_pipeline, g_candidates
        nextWrtc = media.WebRtcEndpoint(g_pipeline)
        wrtc = media.WebRtcEndpoint(g_pipeline, id=g_incoming_end)
        g_session_id = wrtc.get_session_id()
        g_viewers[g_session_id] = nextWrtc

        candidates = g_candidates.get(g_session_id)
        if candidates:
            for c in candidates:
                nextWrtc.add_candidate(c)
            del g_candidates[g_session_id]
        nextWrtc.subscribe('OnIceCandidate', self.handle_candidate)
        sdp_answer = nextWrtc.process_offer(sdp_offer)
        wrtc.connect(nextWrtc)
        nextWrtc.gather_candidates()
        result = {
                    "id": "viewerResponse",
                    "response": "accepted",
                    "sdpAnswer": sdp_answer
                }
        self.write_message(json.dumps(result))

    def presenter(self, sdp_offer):
        global g_session_id, g_pipeline, g_incoming_end
        pipeline = kurento.create_pipeline()
        wrtc = media.WebRtcEndpoint(pipeline)
        g_session_id = wrtc.get_session_id()

        sdp_answer = wrtc.process_offer(sdp_offer)
        wrtc.gather_candidates()
        g_pipeline = pipeline
        g_incoming_end = wrtc.id

        wrtc.subscribe('OnIceCandidate', self.handle_candidate)

        result = {
                    "id": "presenterResponse",
                    "response": "accepted",
                    "sdpAnswer": sdp_answer
                }
        self.write_message(json.dumps(result))

    def handle_candidate(self, event, wrtc):
        self.write_message(json.dumps(event['data']['candidate']))

    def stop(self):
        pass

    def on_ice_candidate(self, candidate):
        global g_incoming_end, g_candidates, g_session_id, g_pipeline
        if g_viewers.get(g_session_id):
            wrtc = g_viewers.get(g_session_id)
            wrtc.add_candidate(candidate)
        elif g_pipeline and g_incoming_end:
            wrtc = media.WebRtcEndpoint(g_pipeline, id=g_incoming_end)
            wrtc.add_candidate(candidate)
        else:
            g_candidates.setdefault(g_session_id, [])
            g_candidates[g_session_id].append(candidate)
