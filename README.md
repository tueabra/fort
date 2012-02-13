# fort

A very simple console replacement for keepass as the alike. It stores everything in a gpg encrypted file.

### Usage

fort can either be run by giving it commands on the console, like this (password query removed for clarity):

    $ ./fort.py set github username tueabra
    Database does iot exist. Creating it...
    $ ./fort.py set github password "you wish" 
    $ ./fort.py set facebook "some random key" "with a random value"
    $ ./fort.py list
     Entries:
      github
      facebook
    $ ./fort.py show github
     Data in entry github
      username: tueabra
      password: you wish

...or by activating the built-in shell:

    $ ./fort.py shell               
    Password: 
    Database does not exist. Creating it...
    fort> set github password "you wish"
    fort> set github username tueabra
    fort> set facebook "some random key" "with a random value"
    fort> list
     Entries:
      github
      facebook
    fort> show github
     Data in entry github
      username: tueabra
      password: you wish
    fort> quit

The biggest reason for using the shell, is that you only need to enter your password once for the session.
