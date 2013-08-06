README
======

Fuzion
------

Fuzion is a new P2P networking library built for Python. Fuzion consists of a developer library, and a
node server to coordinate NAT traversal, connections, and node relations.

Examples
========

Binding and Listening on a port
-------------------------------
		import fuzion

		node = fuzion.Node()
		node.setNodeServer("1.1.1.1:45000")

		# Ports in Fuzion are not integers, but text tags
		port = node.bind("myapp:port")

		connection = port.accept()
		connection.send("Hiya!")
		connection.close()

Connecting to a port
--------------------
		import fuzion

		node = fuzion.Node()
		node.setNodeServer("1.1.1.1:45000")

		connection = node.connect("<hosting node id>", "myapp:port")
		print connection.recv(raw=True)
		connection.close()

License
-------
Fuzion is licensed under the Apache 2.0 license. View the [full license here](http://www.apache.org/licenses/LICENSE-2.0.html)
