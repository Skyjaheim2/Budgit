# Budgit

Budgit is a flask application that allows users to create and manage expenses. This project was created as part of the
CUNY 2021 Hackathon.

![image](https://user-images.githubusercontent.com/64718777/160216067-446397a1-c24f-4685-a368-fa50945cf7fe.png)
![image](https://user-images.githubusercontent.com/64718777/160303805-1ebd427b-d75d-4ab7-b472-29204f84a056.png)
![image](https://user-images.githubusercontent.com/64718777/160303917-244b7ad5-df88-444a-b8de-cda6499cb7ad.png)
![image](https://user-images.githubusercontent.com/64718777/160304024-f3a378fb-3fcd-4c42-bd6d-e03367b9b451.png)
## Requirements

All requirements are listed in requirements.txt.

## Features

* Add expenses to a table which can then be sorted by the date or price.
* Set an expense limit for the day/week/month/year.
* Schedule an expense that gets added automatically at specified times.
* Get notified by email when you have exceeded your expense limit or a schedule expanse has been added.
* Dark mode can be toggled on/off in the accounts page.

## Usage

Visit http://budgitproject.herokuapp.com/ or execute

````
set FLASK_APP=application.py 
flask run
````

## Technologies

* Python Flask
* Vanilla JavaScript

## Testing

Unit tests for the backend are located in the 'Testing' folder and were written using the unittest library.

## Contributors

* https://github.com/Skyjaheim2
* https://github.com/aizatahir

## Contributing

Pull requests are welcome. For major changes, please open an issue first to discuss what you would like to change.

Please make sure to update tests as appropriate.

## License

Licensed under the [MIT License](LICENSE).