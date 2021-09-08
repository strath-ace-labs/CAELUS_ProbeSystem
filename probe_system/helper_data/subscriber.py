from abc import abstractmethod, ABC

class Subscriber(ABC):
    @abstractmethod
    def new_datapoint(self, drone_id, stream_id, datapoint):
        pass
    
    @abstractmethod
    def subscribes_to_streams(self):
        return []