# Driving-Score
# Introduction
This initiative was created in order to prevent accidents caused by drowsiness. When the drowsiness in a driver is detected, the system notifies them right away. Subsequently, it records the date, time, and duration of the drowsiness in a database to create a score that indicates how well the motorist is driving. The project aggressively approaches drivers with high scores to reduces the likelihood of future accidents because prevention is more effective than therapy.
To identify drowsiness in real-time, a custom CNN model is used in this project. The Model achieves 98% accuracy on the testing dataset. To achieve optimal accuracy under all conditions, the training dataset contains low-light, hazy, and spec as well as reflection-filled images and this is done by using the Media Research Lab eye database [MRL Dataset](http://mrl.cs.vsb.cz/eyedataset). It allows the model to detect drowsiness in real-time video with maximum accuracy under all circumstances.
In order to provide a score that provides further insight into a driver's driving abilities, we may also use lane detection and traffic signal infraction detection. 
 

## Installation

Use the package manager [pip](https://pip.pypa.io/en/stable/) to install packages.

```bash
pip install opencv-python
pip install numpy
pip install keras
pip install pygame
pip install mysql-connector-python
pip install tensorflow
```
## Contributing

Pull requests are welcome. For major changes, please open an issue first
to discuss what you would like to change.

Please make sure to update tests as appropriate.
