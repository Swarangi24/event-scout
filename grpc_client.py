# grpc_client.py
import grpc
from grpc_event_pb2 import EventRequest
from grpc_event_pb2_grpc import EventServiceStub


class GRPCClient:
    def __init__(self):
        self.channel = grpc.insecure_channel('localhost:50051')
        self.stub = EventServiceStub(self.channel)

    def fetch_events(self):
        request = EventRequest(query="events")
        response = self.stub.GetEvents(request)
        return response


if __name__ == '__main__':
    client = GRPCClient()
    print(client.fetch_events())