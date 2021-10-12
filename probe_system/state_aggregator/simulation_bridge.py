import asyncio
import mavsdk 
import time 
import threading 
import concurrent
import inspect
from ..helper_data.streams import *

class SimulationBridge():
    def __init__(self, state_aggregator):
        self.state_aggregator = state_aggregator
        self.system = None
        self.__initialised = False

    async def initialise(self, is_done_lock):
        try:
            print(f'Initialising bridge...')
            self.system = mavsdk.System()
            await self.system.connect(system_address="udp://:14540")
        except Exception as e:
            print('Failed in initialising SimulationBridge')
            raise e
        self.__initialised = True
        is_done_lock.acquire()
        is_done_lock.notify()
        is_done_lock.release()
        await self.create_telemetry_tasks()

    def is_initialised(self):
        return self.__initialised

    def telemetry_worker(self, generator, stream_id):

        is_async_gen = hasattr(generator, '__anext__')

        async def __async_worker():
            print(f'[TELEMETRY] stream "{stream_id}" initialised.')
            def dispatch_message(stream_id, data):
                self.state_aggregator.new_datapoint_for_stream(stream_id, data)
            async for data in generator:
                message = (data, f'{time.time()}')
                dispatch_message(stream_id, message)

        async def __worker():
            print(f'[TELEMETRY] stream "{stream_id}" initialised.')
            def dispatch_message(stream_id, data):
                self.state_aggregator.new_datapoint_for_stream(stream_id, data)
            message = (generator(), f'{time.time()}')
            dispatch_message(stream_id, message)

        return __async_worker if is_async_gen else __worker
    
    def get_workers(self):
        workers = {
            S_ACTUATOR_CONTROL_TARGET:self.telemetry_worker(getattr(self.system.telemetry, S_ACTUATOR_CONTROL_TARGET)(), S_ACTUATOR_CONTROL_TARGET),
            S_ACTUATOR_OUTPUT_STATUS:self.telemetry_worker(getattr(self.system.telemetry, S_ACTUATOR_OUTPUT_STATUS)(), S_ACTUATOR_OUTPUT_STATUS),
            S_IS_ARMED:self.telemetry_worker(getattr(self.system.telemetry, S_IS_ARMED)(), S_IS_ARMED),
            S_ATTITUDE_ANGULAR_VELOCITY_BODY:self.telemetry_worker(getattr(self.system.telemetry, S_ATTITUDE_ANGULAR_VELOCITY_BODY)(), S_ATTITUDE_ANGULAR_VELOCITY_BODY),
            S_ATTITUDE_EULER:self.telemetry_worker(getattr(self.system.telemetry, S_ATTITUDE_EULER)(), S_ATTITUDE_EULER),
            S_BATTERY:self.telemetry_worker(getattr(self.system.telemetry, S_BATTERY)(), S_BATTERY),
            S_FIXEDWING_METRICS:self.telemetry_worker(getattr(self.system.telemetry, S_FIXEDWING_METRICS)(), S_FIXEDWING_METRICS),
            S_FLIGHT_MODE:self.telemetry_worker(getattr(self.system.telemetry, S_FLIGHT_MODE)(), S_FLIGHT_MODE),
            S_GPS_GLOBAL_ORIGIN:self.telemetry_worker(getattr(self.system.telemetry, S_GPS_GLOBAL_ORIGIN), S_GPS_GLOBAL_ORIGIN),
            S_GPS_INFO:self.telemetry_worker(getattr(self.system.telemetry, S_GPS_INFO)(), S_GPS_INFO),
            S_GROUND_TRUTH:self.telemetry_worker(getattr(self.system.telemetry, S_GROUND_TRUTH)(), S_GROUND_TRUTH),
            S_HEALTH_STATUS:self.telemetry_worker(getattr(self.system.telemetry, S_HEALTH_STATUS)(), S_HEALTH_STATUS),
            S_HOME_POSITION:self.telemetry_worker(getattr(self.system.telemetry, S_HOME_POSITION)(), S_HOME_POSITION),
            S_IMU_UPDATES_NED:self.telemetry_worker(getattr(self.system.telemetry, S_IMU_UPDATES_NED)(), S_IMU_UPDATES_NED),
            S_IS_IN_AIR:self.telemetry_worker(getattr(self.system.telemetry, S_IS_IN_AIR)(), S_IS_IN_AIR),
            S_IS_LANDED:self.telemetry_worker(getattr(self.system.telemetry, S_IS_LANDED)(), S_IS_LANDED),
            S_POSITION:self.telemetry_worker(getattr(self.system.telemetry, S_POSITION)(), S_POSITION),
            S_POSITION_VELOCITY_NED:self.telemetry_worker(getattr(self.system.telemetry, S_POSITION_VELOCITY_NED)(), S_POSITION_VELOCITY_NED),
            S_UNIX_TIME:self.telemetry_worker(getattr(self.system.telemetry, S_UNIX_TIME)(), S_UNIX_TIME),
            S_STATUS_TEXT:self.telemetry_worker(getattr(self.system.telemetry, S_STATUS_TEXT)(), S_STATUS_TEXT),
            S_GROUND_SPEED_NED:self.telemetry_worker(getattr(self.system.telemetry, S_GROUND_SPEED_NED)(), S_GROUND_SPEED_NED),
        }
        return workers

    def get_available_streams(self):
        return self.get_workers().keys()

    async def create_telemetry_tasks(self):
        workers = self.get_workers()
        loop = asyncio.get_running_loop()
        for i,worker in enumerate(workers.items()):
            worker_stream_id, worker_task = worker
            loop.create_task(worker_task())
