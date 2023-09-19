# RPiMP

Rasberry Pi Manager of Power is tooling that creates a power on and power off through a physical button, and it provides network power on and power for the RPi. This comes close to Wake-on-Lan, but it is not really WoL. Remote power managent is realised through a smart power plug that is managed through ESPHome. The RPi communicaties with the ESP device through `aioesphomeapi`, which is the native API of ESPHome. Power on is by just simply switching the smart plug to on.

## How it works

The ESP device will powerup and and trigger a power down the RPi based on schedules. Shutting down is done via the `delay switch`, which is captured by the RPi. This will start the shutdown on the RPi, but before it does that, it will switch the `real delay switch` to off. The `real delay switch` will wait 15 seconds and then it switches off the power by switching the relay to off. The `real delay switch` is only exposed so the `RPiMP` service can call it, it is best not to be switched manually.

The moment when the `delay switch` is switched off, the RPi will initiate a shutdown. This is done with the `RPiMP` service that runs on the RPi. This serice monitors changes on the ESP through `aioesphome`.

The `delay switch` is also called when the physical button is pressed once. If the physical button is pressed 2 times, the power is immidiately switched off, without going through a sane shutdown on the RPi. This is a failsafe if needed.

Another failsafe is the `heartbeat switch`. This is switched on by RPiMP. If it has not been on for the defined number, the relay will be switched off. If RPiMP crashes for some reason, or loses connection the power will be cut off.

## Why

This is developed for an RPi that needs to be up during schedules. I.e. a backup disk that only needs to be up during backup. It works without Home Assistant, but with Home Assistant it creates a single point of schedule management. There is no need to configure the RPi, only ESP or Home Assistant can manage the power state of the RPi.

## ESPHome smart plug

In the ESPHome folder there is an example on how to configure an `Sonoff S26` smart plug.

## Install RPiMP

Copy the RPiMP folder to the home folder on the RPi. If git is installed:

```bash
git clone https://github.com/Skons/RPiMP
```

Copy the `config.json.example` to `config.json` and edit the file. See [config.json](#configjson)

```bash
cd RPiMP
pip install -r requirements.txt
```

Make sure the path to the `RPiMP` folder in the `RPiMP.service` file is correct.

```bash
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

```bash
curl https://sh.rustup.rs -sSf | sh
source "$HOME/.cargo/env"
```

After it is done rerun the requirements installation. To remove rustup execute:


```bash
rustup self uninstall
```

#### libssl-dev not installed

```
error: could not find system library 'openssl' required by the 'openssl-sys' crate
```

Execute the following command:


```bash
sudo apt install libssl-dev
```

### Configure RPiMP

#### config.json

```json
{
    "Hostname": "sonoffs26", //can be an ip address
    "EncryptionKey": "EncryptionKey", //EncryptionKey configured in the yaml
    "DelaySwitchName": "Sonoff S26 Delay Switch", //friendly name of the delay switch
    "RealDelaySwitchName": "Sonoff S26 Real Delay Switch", //friendly name of the real delay switch
    "HeartbeatSwitchName": "Sonoff S26 Heartbeat Switch", //friendly name of the heartbeat switch
    "LogLevel": "Info", //set logging to info, error, warning and debug
    "LogFile": true //get a log file besides the RPiMP.py as RPiMP.log
}
```

#### ESP Home

The `sonoffs26.yaml` yaml is an example that could be used if you have a Sonoff S26 laying around. If you create your own, please use the `sonoffs26.yaml` as a reference. All sensors, scripts and global from that example are needed to get it all up and running.

#### Time

The time config is for booting and shutting down the RPi. The esp device can, with this configuration, operate completely standalone.

#### Heartbeat

The heartbeat switch is a switche that is switched on bij RPiMP when there is an state update within the ESP device. This update is generally done by the `Current time` text sensor. If the heartbeats are missed for the number defined in `max_heartbeat_missed` in the yaml of your ESP device, the relay will be switched off. It assumes the RPi does not have a connection anymore and therefor it will cut off the power.

## Changelog

### 2023.9.19.1

- Heartbeat introduced
- Documentation updates

### 2023.8.5.1

- Documentation updates
- Minor fixes

### 2023.8.4.1

- Initial release