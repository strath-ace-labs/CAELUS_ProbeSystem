import asyncio
from probe_system.probes.echo_subscriber import EchoSubscriber
from probe_system.state_aggregator.state_aggregator import StateAggregator
from probe_system.helper_data.subscriber import Subscriber

def run(drone_instance_id, subscribers):
    async def __run():
        async with StateAggregator(drone_instance_id) as aggregator:
            for stream_id, subscriber in subscribers:
                aggregator.subscribe(stream_id, subscriber)
            aggregator.report_subscribers()
    return __run

def get_all_subscribers():
    from automatic_probe_import import import_all_probes
    subscribers = []
    for subscriber in import_all_probes(base_class=Subscriber):
        sub_streams = subscriber.subscribes_to_streams()
        for stream_id in sub_streams:
            subscribers.append((stream_id, subscriber))
    return subscribers

if __name__ == '__main__':
    drone_instance_id = 'test_drone'
    subscribers = get_all_subscribers()
    asyncio.run(run(drone_instance_id, subscribers)())

