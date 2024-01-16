# Mechanism Description
The Key-Value-Store tracks causal dependencies with the implementation of vector clocks as a way for the server to stay consistent based on causal metadata. Each replica within the system is initialized with its own vector clock updated each time an event occurs locally or a broadcast is received from a different replica. These vector clocks check whether a replica or client's causal metadata is synchronized with the rest of the system, with the result of this comparison being a denial of service/error or an update to the system. If a replica does not respond to a broadcast from another replica, then it is assumed that this replica is down, and a new update is broadcasted, notifying the other replicas resulting in their "views" being changed to exclude the address of the downed replica so that the system remains entirely functional. 
