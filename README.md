# RPiMP

Rasberry Pi Manager of Power is tooling that creates a power on and power off through a physical button, and it provides network power on and power for the RPi. This comes close to Wake-on-Lan, but it is not really WoL. Remote power managent is realised through a smart power plug that is managed through ESPHome. The RPi communicaties with the ESP device through `aioesphomeapi`, which is the native API of ESPHome. Power on is by just simply switching the smart plug to on.

## How it works

The ESP device will powerup and power down the RPi based on schedules. Upon shutting down the `delay switch` is called, which in his switches the `real delay switch`. They are seperate due to lack of multithread support on an ESP8326. The `real delay switch` will wait 15 seconds and then switch of the power by switching the relay. The `real delay switch` is only exposed so the `RPiMP` can call it.

The moment when the `delay switch` switches off, the RPi will initiate a shutdown. This is done with the `RPiMP` service that runs on the RPi. This serice monitors changes on the ESP through `aioesphome`.

The `delay switch` is also called when the physical button is pressed once. If the physical button is pressed 2 times, the power is immidiately switched off, without going through a sane shutdown on the RPi. This is a failsafe if needed.

## Why

This is developed for an RPi that only needs to be enabled for a specific time, and when there is no Home Assistant around.

## ESPHome smart plug

In the ESPHome folder there is an example on how to configure an `Sonoff S26` smart plug.

## Install RPiMP

Copy the RPiMP folder to the home folder on the RPi. If git is installed:

```
git clone https://github.com/Skons/RPiMP
```

Copy the `config.json.example` to `config.json` and edit the file. See [config.json](#configjson)

```
cd RPiMP
pip install -r requirements.txt
sudo cp RPiMP.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable RPiMP.service
sudo systemctl start RPiMP.service
```

### Installation errors

#### Rust not installed

```
error: can't find Rust compiler
[snip]
ERROR: Failed building wheel for cryptography
```

Rust needs to be installed, execute:

```
curl https://sh.rustup.rs -sSf | sh
source "$HOME/.cargo/env"
```

After it is done rerun the requirements installation. To remove rustup execute:


```
rustup self uninstall
```

#### libssl-dev not installed

```
error: could not find system library 'openssl' required by the 'openssl-sys' crate
```

Execute the following command:


```
sudo apt install libssl-dev
```

### config.json

After installation, edit the `config.json`

```json
{
    "Hostname": "sonoffs26", //can be an ip address
    "EncryptionKey": "EncryptionKey", //EncryptionKey configured in the yaml
    "DelaySwitchName": "Sonoff S26 Delay Switch", //friendly name of the delay switch
    "RealDelaySwitchName": "Sonoff S26 Real Delay Switch", //friendly name of the real delay switch
    "LogLevel": "Info", //set logging to info, error, warning and debug
    "LogFile": true //get a log file besides the RPiMP.py as RPiMP.log
}
```