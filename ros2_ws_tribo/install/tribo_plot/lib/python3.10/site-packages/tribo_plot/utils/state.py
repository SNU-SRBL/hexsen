import numpy as np

class StateManager():
    def __init__(self):
        self.__state = 'idle'
        self.last_state = 'idle'
        self.event = 0
        self.buffer = np.zeros((4,1000))
        self.touch_buffer = np.zeros((4, 1000))

    @property
    def state(self):
        """Getter for the 'state' attribute."""
        return self.__state
    
    @state.setter
    def state(self, value):
        """Setter for the 'state' attribute."""
        if value not in ['idle', 'touch', 'stay', 'slide', 'detach']:
            raise ValueError(f"Invalid state: {value}")
        self.__state = value

    def callback(self, data):
        self.buffer = data.copy()

    def metric_touch(self):
        data = self.buffer.copy()
        metric = np.mean(np.sum(data, axis=1)) # mean of (4, 1) shape
        if metric > 20:
            self.touch_buffer = data.copy()
        return metric

    def metric_slide(self, data):
        metric = np.mean(np.abs(np.mean(data, axis=1))) # mean of abs((4,1)) shape
        return metric


    # if state != self.last_state:
    # self.get_logger().info(f"State changed: {self.last_state} -> {state}")
    # self.last_state = state

if __name__ == "__main__":
    sm = StateManager()
    print(sm.state)         # Output: idle

    sm.state = 'touch'
    print(sm.state)         # Output: touch

    try:
        sm.state = 'flying'   # Not allowed; will raise ValueError
    except ValueError as e:
        print(e)