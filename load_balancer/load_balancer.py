from abc import ABC, abstractmethod
from uuid import UUID


class Server:
    def __init__(self, id: UUID, address: str) -> None:
        self.id = id
        self.address = address
        self.active_connections: int = 0

    def incr_connections(self):
        self.active_connections += 1

    def decr_connections(self):
        if self.active_connections <= 0:
            raise ValueError("No active connections")
        self.active_connections -= 1

    def update_address(self, address: str):
        if not address or not address.strip():
            raise ValueError("Address cannot be empty")
        self.address = address


class DistributionAlgorithm(ABC):
    @abstractmethod
    def balance(self) -> Server:
        pass

    @abstractmethod
    def add_server(self, server: Server):
        pass

    @abstractmethod
    def remove_server(self, server: Server):
        pass


class RoundRobin(DistributionAlgorithm):
    def __init__(self, servers: dict[UUID, Server]):
        self._servers = list(servers.values())
        self.index = 0

    def balance(self) -> Server:
        if not self._servers:
            raise Exception("No servers available")
        
        server = self._servers[self.index]
        self.index = (self.index + 1) % len(self._servers)
        return server

    def add_server(self, server: Server):
        self._servers.append(server)

    def remove_server(self, server: Server):
        for i, s in enumerate(self._servers):
            if s.id != server.id:
                continue

            self._servers.pop(i)

            if not self._servers:
                self.index = 0
                return

            self.index %= len(self._servers)
            return


class LeastConn(DistributionAlgorithm):
    def __init__(self, servers: dict[UUID, Server]):
        self._servers = list(servers.values())

    def balance(self) -> Server:
        if not self._servers:
            raise RuntimeError("No servers available")
        return min(self._servers, key=lambda serv: serv.active_connections)

    def add_server(self, server: Server):
        self._servers.append(server)

    def remove_server(self, server: Server):
        for i, s in enumerate(self._servers):
            if s.id == server.id:
                self._servers[-1], self._servers[i] = self._servers[i], self._servers[-1]
                self._servers.pop()
                break

class LoadBalancer:
    def __init__(self, servers: dict[UUID, Server], distributor: DistributionAlgorithm) -> None:
        self.distributor = distributor
        self.servers = servers

    def get_server(self) -> Server:
        server = self.distributor.balance()
        server.incr_connections()
        return server
    
    def release_server(self, server: Server):
        server.decr_connections()
        
    def add_server(self, server: Server) -> None:
        if server.id in self.servers:
            raise ValueError("Server already exists")

        self.servers[server.id] = server
        self.distributor.add_server(server)

    def remove_server(self, server: Server) -> None:
        if server.id not in self.servers:
            raise ValueError("Server not found")

        del self.servers[server.id]
        self.distributor.remove_server(server)