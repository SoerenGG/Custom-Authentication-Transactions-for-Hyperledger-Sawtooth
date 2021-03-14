# Custom-Authentication-Transactions-for-Hyperledger-Sawtooth
## Set up a Sawtooth Network
1. First a Sawtooth Network has to be set up, following the link for the explanation and the corresponding repo:
* https://sawtooth.hyperledger.org/docs/core/releases/latest/app_developers_guide.html
* https://github.com/hyperledger/sawtooth-core  
## How to use the Accumulator Client and Authentication Transaction Processer of this Repository: 
1. install by changing in this directory and run: "pyhton3 setup.py install"
2. open new terminal and connect to validator: "custom-authentication-tp-python --connect tcp://validator:4004"
3. open new terminal and create keys: "sawtooth keygen" and stay here
    * accumulator-manager-client cmd is = "accumulator-manager"
        * "accumulator-manager initialize \<servicename\>"
    * user-client gets called through accmulator-manager-client
        * "accumulator-manager user-client-add \<username\> \<servicename\>"
        * "accumulator-manager user-client-remove \<username\> \<servicename\>"
        * "accumulator-manager user-client-authenticate \<username\> \<servicename\>"
4. initialize new Accumulator with a servicename, the accumulator value has to be 9 (eg "mercedes"):
    1. "accumulator-manager initialize mercedes 9"
5. add a user to the accumulator by specifying the service the user wants to be added to and give a username (eg "user1")
    1. "acaccumulator-manager user-client-add user1 mercedes"
6. verify membership of a user for a service
    1. ""acaccumulator-manager user-client-authenticate user1 mercedes"
