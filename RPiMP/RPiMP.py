import asyncio
import logging
from logging.handlers import RotatingFileHandler
import json
import os, sys
from aioesphomeapi import (
	APIClient,
	APIConnectionError,
	ReconnectLogic,
)

async def main():
	global delay_switch,real_delay_switch,is_disconnected

	def get_config():
		"""Parse config from a JSON file"""
		f = open('config.json')
		data = json.load(f)
		f.close()
		return data

	def change_callback(state):
		"""Capture the change of the delay switch, trigger the real delay switch and shutdown the system"""
		global delay_switch,real_delay_switch
		if state.key == delay_switch.key and state.state == False:
			logging.info(f"Delay switch '{delay_switch.name}' is switched off, switching '{real_delay_switch.name}' with key '{real_delay_switch.key}' to off")
			coro = cli.switch_command(real_delay_switch.key,False)
			asyncio.get_event_loop().create_task(coro).add_done_callback(initiate_shutdown) #change_callback is not async, this solution solves that problem

	def initiate_shutdown(task):
		"""Handle shutdown"""
		logging.info("Initiating shutdown")
		os.system("sudo shutdown -P now")

	async def on_connect() -> None:
		"""Try to find the delay and real delay switch based on the friendly name from the config. Then trigger change_callback for entity changes."""
		global delay_switch,real_delay_switch,is_disconnected
		entities = await cli.list_entities_services()
		logging.debug(f"Found '{entities[0].count}' entities")
		for entity in entities[0]:
			if entity.name == delay_switch_name:
				logging.info(f"Found delay switch '{entity.name}' with id '{entity.object_id}' and key '{entity.key}'")
				delay_switch = entity
			elif entity.name == real_delay_switch_name:
				logging.info(f"Found real delay switch '{entity.name}' with id '{entity.object_id} and key '{entity.key}'")
				real_delay_switch = entity
			else:
				logging.debug(f"Ignoring '{entity.object_id}' with name '{entity.name}'")

		if delay_switch == None:
			error = f"Unable to find delay switch with name '{delay_switch_name}'"
			logging.error(error)
			raise Exception(error)
		if real_delay_switch == None:
			error = f"Unable to find real delay switch with name '{real_delay_switch_name}'"
			logging.error(error)
			raise Exception(error)

		logging.debug(f"Key to watch for delay switch '{delay_switch.name}' is '{delay_switch.key}'")
		logging.debug(f"Key to toggle real delay switch '{real_delay_switch.name}' is '{real_delay_switch.key}'")

		is_disconnected = False

		try:
			await cli.subscribe_states(change_callback)
		except APIConnectionError as err:
			logging.warning("Error getting initial data for %s: %s", host, err)
			# Re-connection logic will trigger after this
			await cli.disconnect()

	async def on_disconnect(expected_disconnect) -> None:
		"""Run disconnect stuff on API disconnect."""
		global is_disconnected
		logging.info(f"Disconnected changed to '{expected_disconnect}'")
		is_disconnected = expected_disconnect

	async def on_connect_error(err: Exception) -> None:
		"""Show connection errors."""
		logging.error(f"Failed to connect with error '{err}'")

	async def disconnect_watchdog():
		"""Detect if there is no connection for a defined period. This is needed if the ESP device gets an update. The reconnect_logic will not reconnect when this happens"""
		global is_disconnected
		counter = -1 #This function runs before the ESP is connected on start
		wait_time_in_seconds = 3
		max_wait_in_minutes = 5
		max_counter = int((60 * max_wait_in_minutes) / wait_time_in_seconds)
		while True:
			if is_disconnected:
				counter+=1
				if counter == 1:
					logging.warning(f"RPiMP current state is disonnected, watchdog will restart service after '{max_wait_in_minutes}' minutes if state continues.")
				logging.debug(f"Disconnected state change detected, current counter '{counter}'. Restarting service after counter '{max_counter}', which is '{max_wait_in_minutes}' minutes.")
				if counter >= max_counter:
					logging.error(f"RPiMP not connected to '{host}'. '{max_wait_in_minutes}' minutes have expired, restarting RPiMP.service")
					os.system("sudo systemctl restart RPiMP.service")
					sys.exit(0)
			elif counter != 0:
				logging.info(f"Connection (re)established, setting disconnect counter '{counter}' to 0")
				counter = 0
			await asyncio.sleep(wait_time_in_seconds)

	#Initialize variables
	config = get_config()
	host = config['Hostname']
	encryption_key = config['EncryptionKey']
	client_name = "RPiMP"
	client_info = f"{client_name} 2023.8.1.1"

	delay_switch = None
	real_delay_switch = None

	is_disconnected = True

	delay_switch_name = config['DelaySwitchName']
	real_delay_switch_name = config['RealDelaySwitchName']
	password = None
	if "Password" in config and config['Password']:
		password = config['Password']

	# Initialize logger
	log_level = logging.INFO
	if "LogLevel" in config and config['LogLevel'].lower() == "debug":
		log_level = logging.DEBUG
	elif "LogLevel" in config and config['LogLevel'].lower() == "warning":
		log_level = logging.WARNING
	elif "LogLevel" in config and config['LogLevel'].lower() == "error":
		log_level = logging.ERROR
	handlers=[
		logging.StreamHandler()
	]
	if config['LogFile'] == True:
		handlers += [RotatingFileHandler(filename="RPiMP.log",mode='w', maxBytes=512000, backupCount=4)]

	logging.basicConfig(
		level=log_level,
		format="%(asctime)s [%(levelname)s] %(message)s",
		handlers=handlers
	)

	#Define aioesphome API client
	cli = APIClient(
		host,
		6053,
		password,
		client_info=client_info,
		noise_psk=encryption_key,
	)

	#Build reconnect logic
	reconnect_logic = ReconnectLogic(
		client=cli,
		on_connect=on_connect,
		on_disconnect=on_disconnect,
		zeroconf_instance=None,
		name=client_name,
		on_connect_error=on_connect_error,
	)

	await reconnect_logic.start()
	await disconnect_watchdog()

#Run async loop
loop = asyncio.get_event_loop()
try:
	asyncio.ensure_future(main())
	loop.run_forever()
except KeyboardInterrupt:
	pass
finally:
	loop.close()