# ToyChord-DHT-File-Sharing
Final Assignment for Distributed Systems NTUA 2020-2021

In this project we implemented ToyChord, a simplified Chord[[1]](#1) version. The ToyChord is a distributed lookup system that can be used as a peer-to-peer file sharing system. Data is stored as key-value pairs in a set of distributed hash table (DHT) nodes. Each node implements every DHT function, such as to create server and client processes, to open sockets and to answer incoming requests. ToyChord efficintly handles node insertions, node departures, data replication and the answering of requests, even if the DHT system is changing dynamically. 


## References

<a id="1">[1]</a> 
Stoica, Ion, et al. "Chord: A scalable peer-to-peer lookup service for internet applications." ACM SIGCOMM Computer Communication Review 31.4 (2001): 149-160.
