# ATM Simulation
### A project by Tristan Gurtler, Charissa Miller, Kendall Molas, and Lynn Wu during the NYIT REU 2017 session.

This project recreates an ATM PIN entry screen on a webserver that also records users' keystrokes, in order to determine if side-channel attacks are viable on ATMs. Specifically, we seek to test whether or not, by determining the timing between keystrokes, we can extract information about what PINs could possibly fit these interkey timings, and reduce the possible space of PINs to try. This tool, then, collects the interkey timings we will use to test this.

This tool is used in coordination with video processing software to determine if we can reliably reconstruct interkey timings from a video feed of a user typing in their PIN (as in, say, an attacker with a video camera pointed at the screen watching for asterisks to appear), and machine learning software to match interkey timings to possible keypairs in the PIN.

This tool, when dropped into place to use as a server for a webapp, requires no setup (just run it).

## Routes:

This tool defines URL routings to use on the webapp, with certain functionalities.

### User-facing

This tool is only publicly accessible from "/" and "/get_uid" until an experiment has begun. Going to these directories will prompt a user to give a numeric ID. The tool will then validate that the ID is valid, and route the user through the experiment (which has a practice phase, and several PIN entry phases). At the end, a short "thank you" screen will be displayed, after which the site will revert back to the "/" page. Web browsers used for this must support asynchronous Javascript functions.

### Admin-facing

This tool is accessible through an easily adapted username and password for some functions.
**"/reset_db"**: Resets/creates the database tables used for recording keystroke data during the experiment.
**"/reset_attempts"**: Resets the keystroke data collected (useful to clear out data when modifying parts of the experiment).
**"/reset_user/<user_id>"**: Resets the number of attempts recorded for a user (which will return them back to the first set of PINs, if necessary).
**"/make_user"**: Create (and set up in the DB) a new user, specifying what group they will be a part of.