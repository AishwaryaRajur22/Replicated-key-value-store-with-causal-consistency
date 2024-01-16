# Team Contributions

## Camren Coleman
### Primary contributor for assignment. Worked on testing/debugging, broadcasting, and replica updates.

## Jed Valeika 
### Helped with initial setup/outline and facilitation of group work.

## Aishwarya Rajur

### Worked on vector clock and causal consistency needs.
# Acknowledgements
### N/A
# Citations

### Used google search for issues relating to syntax, semantics, and educational purposes. Also used chatGPT occasionally for guidance and debugging.

# Mechanism Description
### Our KVS store tracks causal dependencies with the implementation of vector clocks as a way for our server to stay consistent based on causal metadata. Each replica within the system is initialized with it's own vector clock that is updated each time an event occurs locally or a broadcast is received from a different replica. These vector clocks check whether a replica or client's causal metadata is synchronized with the rest of the system with the result of this comparison being denial of service/error or an update to the system. If a replica does not respond to a broadcast from another replica, then it is assumed that this replica is down and a new update is broadcasted notifying the other replicas resulting in their "views" being changed to exclude the address of the downed replica so that the system remains entirely functional. 
