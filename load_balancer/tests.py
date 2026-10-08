from uuid import uuid4

import pytest

from load_balancer import (
    Server,
    RoundRobin,
    LeastConn,
    LoadBalancer,
)


def make_server(address: str) -> Server:
    return Server(uuid4(), address)


# ============================================================
# Server
# ============================================================


def test_server_initial_state():
    server = make_server("10.0.0.1")

    assert server.active_connections == 0
    assert server.address == "10.0.0.1"


def test_server_increment_connections():
    server = make_server("10.0.0.1")

    server.incr_connections()
    server.incr_connections()

    assert server.active_connections == 2


def test_server_decrement_connections():
    server = make_server("10.0.0.1")

    server.incr_connections()
    server.incr_connections()
    server.decr_connections()

    assert server.active_connections == 1


def test_server_cannot_decrement_without_connections():
    server = make_server("10.0.0.1")

    with pytest.raises(ValueError, match="No active connections"):
        server.decr_connections()


def test_server_update_address():
    server = make_server("10.0.0.1")

    server.update_address("10.0.0.2")

    assert server.address == "10.0.0.2"


def test_server_rejects_empty_address():
    server = make_server("10.0.0.1")

    with pytest.raises(ValueError, match="Address cannot be empty"):
        server.update_address("")


def test_server_rejects_whitespace_address():
    server = make_server("10.0.0.1")

    with pytest.raises(ValueError, match="Address cannot be empty"):
        server.update_address("   ")


# ============================================================
# Round Robin
# ============================================================


def test_round_robin_distributes_in_order():
    s1 = make_server("10.0.0.1")
    s2 = make_server("10.0.0.2")
    s3 = make_server("10.0.0.3")

    algorithm = RoundRobin({
        s1.id: s1,
        s2.id: s2,
        s3.id: s3,
    })

    assert algorithm.balance() is s1
    assert algorithm.balance() is s2
    assert algorithm.balance() is s3
    assert algorithm.balance() is s1
    assert algorithm.balance() is s2


def test_round_robin_empty():
    algorithm = RoundRobin({})

    with pytest.raises(Exception, match="No servers available"):
        algorithm.balance()


def test_round_robin_add_server():
    s1 = make_server("10.0.0.1")
    s2 = make_server("10.0.0.2")

    algorithm = RoundRobin({
        s1.id: s1,
    })

    algorithm.add_server(s2)

    assert algorithm.balance() is s1
    assert algorithm.balance() is s2
    assert algorithm.balance() is s1


def test_round_robin_remove_server():
    s1 = make_server("10.0.0.1")
    s2 = make_server("10.0.0.2")
    s3 = make_server("10.0.0.3")

    algorithm = RoundRobin({
        s1.id: s1,
        s2.id: s2,
        s3.id: s3,
    })

    algorithm.remove_server(s2)

    assert algorithm.balance() is s1
    assert algorithm.balance() is s3
    assert algorithm.balance() is s1


def test_round_robin_remove_all_servers():
    s1 = make_server("10.0.0.1")

    algorithm = RoundRobin({
        s1.id: s1,
    })

    algorithm.remove_server(s1)

    with pytest.raises(Exception, match="No servers available"):
        algorithm.balance()


# ============================================================
# Least Connections
# ============================================================


def test_least_connections_selects_server_with_fewest_connections():
    s1 = make_server("10.0.0.1")
    s2 = make_server("10.0.0.2")
    s3 = make_server("10.0.0.3")

    s1.active_connections = 5
    s2.active_connections = 2
    s3.active_connections = 8

    algorithm = LeastConn({
        s1.id: s1,
        s2.id: s2,
        s3.id: s3,
    })

    assert algorithm.balance() is s2


def test_least_connections_selects_zero_connection_server():
    s1 = make_server("10.0.0.1")
    s2 = make_server("10.0.0.2")

    s1.active_connections = 10
    s2.active_connections = 0

    algorithm = LeastConn({
        s1.id: s1,
        s2.id: s2,
    })

    assert algorithm.balance() is s2


def test_least_connections_empty():
    algorithm = LeastConn({})

    with pytest.raises(RuntimeError, match="No servers available"):
        algorithm.balance()


def test_least_connections_add_server():
    s1 = make_server("10.0.0.1")
    s2 = make_server("10.0.0.2")

    s1.active_connections = 10
    s2.active_connections = 0

    algorithm = LeastConn({
        s1.id: s1,
    })

    algorithm.add_server(s2)

    assert algorithm.balance() is s2


def test_least_connections_remove_server():
    s1 = make_server("10.0.0.1")
    s2 = make_server("10.0.0.2")
    s3 = make_server("10.0.0.3")

    s1.active_connections = 10
    s2.active_connections = 2
    s3.active_connections = 5

    algorithm = LeastConn({
        s1.id: s1,
        s2.id: s2,
        s3.id: s3,
    })

    algorithm.remove_server(s2)

    assert algorithm.balance() is s3


# ============================================================
# Load Balancer
# ============================================================


def test_load_balancer_get_server_increments_connections():
    s1 = make_server("10.0.0.1")

    distributor = RoundRobin({
        s1.id: s1,
    })

    balancer = LoadBalancer(
        {s1.id: s1},
        distributor,
    )

    assert s1.active_connections == 0

    server = balancer.get_server()

    assert server is s1
    assert s1.active_connections == 1


def test_load_balancer_release_server_decrements_connections():
    s1 = make_server("10.0.0.1")

    distributor = RoundRobin({
        s1.id: s1,
    })

    balancer = LoadBalancer(
        {s1.id: s1},
        distributor,
    )

    server = balancer.get_server()

    assert server.active_connections == 1

    balancer.release_server(server)

    assert server.active_connections == 0


def test_load_balancer_round_robin():
    s1 = make_server("10.0.0.1")
    s2 = make_server("10.0.0.2")

    distributor = RoundRobin({
        s1.id: s1,
        s2.id: s2,
    })

    balancer = LoadBalancer(
        {
            s1.id: s1,
            s2.id: s2,
        },
        distributor,
    )

    assert balancer.get_server() is s1
    assert balancer.get_server() is s2
    assert balancer.get_server() is s1

    assert s1.active_connections == 2
    assert s2.active_connections == 1


def test_load_balancer_least_connections():
    s1 = make_server("10.0.0.1")
    s2 = make_server("10.0.0.2")

    distributor = LeastConn({
        s1.id: s1,
        s2.id: s2,
    })

    balancer = LoadBalancer(
        {
            s1.id: s1,
            s2.id: s2,
        },
        distributor,
    )

    first = balancer.get_server()
    second = balancer.get_server()

    assert first is s1
    assert second is s2

    assert s1.active_connections == 1
    assert s2.active_connections == 1


def test_load_balancer_add_server():
    s1 = make_server("10.0.0.1")
    s2 = make_server("10.0.0.2")

    distributor = RoundRobin({
        s1.id: s1,
    })

    balancer = LoadBalancer(
        {
            s1.id: s1,
        },
        distributor,
    )

    balancer.add_server(s2)

    assert s2.id in balancer.servers
    assert balancer.servers[s2.id] is s2

    assert balancer.get_server() is s1
    assert balancer.get_server() is s2


def test_load_balancer_rejects_duplicate_server():
    s1 = make_server("10.0.0.1")

    distributor = RoundRobin({
        s1.id: s1,
    })

    balancer = LoadBalancer(
        {
            s1.id: s1,
        },
        distributor,
    )

    with pytest.raises(ValueError, match="Server already exists"):
        balancer.add_server(s1)


def test_load_balancer_remove_server():
    s1 = make_server("10.0.0.1")
    s2 = make_server("10.0.0.2")

    distributor = RoundRobin({
        s1.id: s1,
        s2.id: s2,
    })

    balancer = LoadBalancer(
        {
            s1.id: s1,
            s2.id: s2,
        },
        distributor,
    )

    balancer.remove_server(s2)

    assert s2.id not in balancer.servers

    assert balancer.get_server() is s1
    assert balancer.get_server() is s1


def test_load_balancer_rejects_missing_server():
    s1 = make_server("10.0.0.1")
    s2 = make_server("10.0.0.2")

    distributor = RoundRobin({
        s1.id: s1,
    })

    balancer = LoadBalancer(
        {
            s1.id: s1,
        },
        distributor,
    )

    with pytest.raises(ValueError, match="Server not found"):
        balancer.remove_server(s2)


def test_round_robin_remove_current_position():
    s1 = make_server("10.0.0.1")
    s2 = make_server("10.0.0.2")
    s3 = make_server("10.0.0.3")

    algorithm = RoundRobin({
        s1.id: s1,
        s2.id: s2,
        s3.id: s3,
    })

    assert algorithm.balance() is s1

    algorithm.remove_server(s2)

    assert algorithm.balance() is s3
    assert algorithm.balance() is s1
    assert algorithm.balance() is s3