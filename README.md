# Micromath

Toy microservice architecture for 3 math operations: exponentiation, fibonacci and factorial

### Requirements
1. Python >=3.6
2. Docker

### Installation

```bash
python setup.py install
```

### Build

```bash
docker-compose up -d
```

### Example usage

```python
import requests
sess = requests.Session()

sess.post('http://localhost:8080/login', data={'username': 'null', 'password': 'null'})
result = sess.post('http://localhost:8080/api/v1/pow', json={'base': 2, 'power': 3})

logs = sess.get('http://localhost:8080/api/v1/logs?page=1')
```


### Destory

```bash
docker-compose down --rmi all
```


### Architecture

<p align="center">
  <img src="docs/micromath_arch.png">
</p>


### TODO

* Better login password comparison
* Reverse proxy (nginx)
* Unit testing
* TLS support
* Refactor the routes with Viewes, they can achieve better code quality than routes
* Use docker swarm mode to work with services and be able to scale containers
