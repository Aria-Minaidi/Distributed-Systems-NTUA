# ToyChord-DHT-File-Sharing
Final Assignment for Distributed Systems NTUA 2020-2021

In this project we implemented ToyChord, a simplified Chord[[1]](#1) version. The ToyChord is a distributed lookup system that can be used as a peer-to-peer file sharing system. Data are stored as key-value pairs in a set of distributed hash table (DHT) nodes. Each node implements every DHT function, such as to create server and client processes, to open sockets and to answer incoming requests. ToyChord efficintly handles node insertions, node departures, data replication and the answering of requests, even if the DHT system is changing dynamically. 

Every **key** is generated based on the name of a file and it is inserted into the DHT. Our keyspace, which representsthe range of possible hashes, is between 0 and 2m-1, where m is defined by MAX_BITS in our code (we have m=10, which makes our keyspace to be 0-1023). 

The commands and functions are: 
* Join: join the network/connect to bootstrap node.
* Insert: insert <key, value> (eg. ('ntua', 1)).
* Delete: delete <key> from DHT network.
* Depart: exits from network's topology.
* Query: Query <key> (special case * prints every key,value on DHT).
* Overlay: prints network topology.
* Succ/pred: Prints ID,succesor,predecessor of given node.
* read_insert: Execute insert.txt for given node.
* read_query: Execute query.txt for given node.
* read_requests: Execute requests.txt for given node.



## References

<a id="1">[1]</a> 
Stoica, Ion, et al. "Chord: A scalable peer-to-peer lookup service for internet applications." ACM SIGCOMM Computer Communication Review 31.4 (2001): 149-160.
