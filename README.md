# Open Source Voting Platform
A secure voting platform with provable votes for use in any voting scenario.

## Goals
To provide a secure voting system with the capability to make results accessible for 3rd party analysis without exposing personal information attached to the votes. Individuals will be able to verify their own votes as well after the fact, while any individual can also verify the results as a whole. 

These features will be considered critical, but will also be an optional part of the actual voting system which will be built use either its own built in authentication system or existing systems.

## Specific Deliverables
### Senate Voting System
This system will be put into use with the RPI Student senate to be used during meetings to facilitate quorum checking and easy voting. Additionaly features will include keeping a voter history and allowing for the voting populace to see the history of their elected officials.

A general list of features we are considering:
- Voting history.
- Quorum checking.
- Vote types (2/3s, simple majority)
- Attendance system and administrative panel for live creation of questions.
- Auto-pulling voting page so that way one page can be kept open as new votes arise.
- Ye / Ney display for live feedback.
- Other cool statistics.
- Senator verification.

### Elections Voting System
The RPI Student Government elections moved to electronic voting last year. The system worked well, but issues involving its closed source nature along with general hesistations involving electronic voting have led to us redesiging the system in an open source manner.

## Proving the Vote
An issue often found with electronic voting is that the votes could be tamperred with without physical evidence or proof that results were altered. Our voting platform wishes to issue each voter an anonymous key. 

## Credits

This project was created for use by the Rensselaer Union Student Senate by the Web Technologies Group.

### Developers

* [David Raab](http://github.com/draab)
* [Mason Cooper](http://github.com/not-inept)
* [Justin Etzine](http://github.com/justetz)

###From Original Repo
Run:

```
meteor --settings=settings.json
```

Users are created from `users.json` file. For each user an e-mail is send with an invitation
to set a password. `users.json` file is also used to configure which users are facilitators.
