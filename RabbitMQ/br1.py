import pika
from pika.exchange_type import ExchangeType
import os
from redis import Redis
import json
cli = Redis('localhost')
connection_parameters = pika.ConnectionParameters('localhost')
connection = pika.BlockingConnection(connection_parameters)

channel = connection.channel()
queue = channel.queue_declare(queue='', exclusive=True)
channel.exchange_declare(exchange='routing', exchange_type=ExchangeType.direct)
channel.queue_bind(exchange='routing',queue=queue.method.queue,routing_key='zookeeper')


channel2 = connection.channel()
queue2 = channel.queue_declare(queue='', exclusive=True)
channel2.exchange_declare(exchange='routing2', exchange_type=ExchangeType.direct)



def open_required_queues():    
    lino = json.loads(cli.get('leadership')) 
    for topic in lino:
        num_part = lino[topic][0]
        for i in range(1,num_part+1):
            if(lino[topic][i]==1):
                channel.queue_bind(exchange='routing', queue=queue.method.queue, routing_key=f'1/{topic}/partition{i}')   
            else:
                channel2.queue_bind(exchange='routing2', queue=queue2.method.queue, routing_key=f'1/{topic}/partition{i}')
                
                

def on_message_received(ch, method, properties, body): 
    if(method.routing_key=="zookeeper"):
        print(f"Broker - received new message: {body}")
        open_required_queues()
    else:
        
            print(f"Broker - received new message: {body}")
            os.makedirs(f'{method.routing_key}', exist_ok=True)
            f = open(f"{method.routing_key}/log.txt", "a")
            f.write(str(body))
            f.close() 
            channel2.basic_publish(exchange='routing2', routing_key="3"+method.routing_key[1:], body=str(body))
            channel2.basic_publish(exchange='routing2', routing_key="2"+method.routing_key[1:], body=str(body))
        

def omr(ch, method, properties, body):
            os.makedirs(f'{method.routing_key}', exist_ok=True)
            f = open(f"{method.routing_key}/log.txt", "a")
            f.write(str(body))
            f.close() 

channel.basic_consume(queue=queue.method.queue, auto_ack=True,
    on_message_callback=on_message_received)

channel2.basic_consume(queue=queue2.method.queue, auto_ack=True,
    on_message_callback=omr)

print("Broker 1 running")

channel.start_consuming()
channel2.start_consuming()