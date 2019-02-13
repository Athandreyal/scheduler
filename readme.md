[//]: # (written using https://dillinger.io/)


# UofC Class Schedule Information Scraper

This is a python script which will parse the University of Calgary website for class requisites and class schedules information.

It will keep local copies of every file it cares about, and will only resort to a web request if it has nothing locally.

 - first it tries for a local object file, these were output tofile previously via jsonpickle
 - failing to load that,it will remove the local object file if it exists(may be broken), and will reparse local html
 - if there is no local html, it will perform the html request to go get it.

Web requests are deliberately slowed with 1-5 second sleeps, selected randomly, to reduce the chance of getting rejected by anti-spam measures on UofC's webserver.

Should a request fail three times, it will go into rejected mode, and will sleep for a predetermined time starting at 2.5 minutes.

Every successive triple fail of requests increases the duration of both the per request and pre rejection delays, to feel out appropriate values.

### Required
This script was written under python 3.7, no attempt to verfy functionality on older versions has been made.
JsonPickle is required for this script to function.

Get it here: [JsonPickle](https://jsonpickle.github.io/).

```sh
$ pip install -U jsonpickle
```
or you can get it from the source and simply run:
```sh
$ python setup.py install
```