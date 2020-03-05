from ledfx.config import save_config
from ledfx.api import RestEndpoint
from aiohttp import web
import logging
import json

_LOGGER = logging.getLogger(__name__)

class DevicePresetsEndpoint(RestEndpoint):

    ENDPOINT_PATH = "/api/devices/{device_id}/presets"

    async def get(self, device_id) -> web.Response:
        """get active effect for a device"""
        device = self._ledfx.devices.get(device_id)
        if device is None:
            response = { 'not found': 404 }
            return web.Response(text=json.dumps(response), status=404)

        # Get the active effect
        response = { 'effect' : {}}
        if device.active_effect:
            effect_response = {}
            effect_response['config'] = device.active_effect.config
            effect_response['name'] = device.active_effect.name
            effect_response['type'] = device.active_effect.type
            response = { 'effect' : effect_response }

        return web.Response(text=json.dumps(response), status=200)

    async def put(self, device_id, request) -> web.Response:
        """set active effect of device to a preset"""
        device = self._ledfx.devices.get(device_id)
        if device is None:
            response = { 'not found': 404 }
            return web.Response(text=json.dumps(response), status=404)

        data = await request.json()
        effect_id = data.get('effect_id')
        preset_id = data.get('preset_id')

        if effect_id is None:
            response = { 'status' : 'failed', 'reason': 'Required attribute "effect_id" was not provided' }
            return web.Response(text=json.dumps(response), status=500)

        if not effect_id in self._ledfx.config['presets'].keys():
            response = { 'status' : 'failed', 'reason': 'Effect {} has no presets'.format(preset_id) }
            return web.Response(text=json.dumps(response), status=500)

        if preset_id is None:
            response = { 'status' : 'failed', 'reason': 'Required attribute "preset_id" was not provided' }
            return web.Response(text=json.dumps(response), status=500)

        if not preset_id in self._ledfx.config['presets'][effect_id].keys():
            response = { 'status' : 'failed', 'reason': 'Preset {} does not exist for effect {}'.format(preset_id, effect_id) }
            return web.Response(text=json.dumps(response), status=500)

        # Create the effect and add it to the device
        effect_config = self._ledfx.config['presets'][effect_id][preset_id]['config']
        effect = self._ledfx.effects.create(
            ledfx = self._ledfx,
            type = effect_id,
            config = effect_config)
        device.set_effect(effect)

        # Update and save the configuration
        for device in self._ledfx.config['devices']:
            if (device['id'] == device_id):
                #if not ('effect' in device):
                device['effect'] = {}
                device['effect']['type'] = effect_type
                device['effect']['config'] = effect_config
                break
        save_config(
            config = self._ledfx.config, 
            config_dir = self._ledfx.config_dir)

        effect_response = {}
        effect_response['config'] = effect.config
        effect_response['name'] = effect.name
        effect_response['type'] = effect.type

        response = { 'status' : 'success', 'effect' : effect_response}
        return web.Response(text=json.dumps(response), status=200)

    async def post(self, device_id, request) -> web.Response:
        """save configuration of active device effect as a preset"""
        device = self._ledfx.devices.get(device_id)
        if device is None:
            response = { 'not found': 404 }
            return web.Response(text=json.dumps(response), status=404)

        if not device.active_effect:
            response = { 'status' : 'failed', 'reason': 'device {} has no active effect'.format(device_id) }
            return web.Response(text=json.dumps(response), status=404)

        data = await request.json()
        preset_name = data.get('name')
        if preset_name is None:
            response = { 'status' : 'failed', 'reason': 'Required attribute "preset_name" was not provided' }
            return web.Response(text=json.dumps(response), status=500)

        preset_id = generate_id(preset_name)

        # If no presets for the effect, create a dict to store them
        if not effect_id in self._ledfx.config['presets'].keys():
            self._ledfx.config['presets'][effect_id] = {}

        # Update the preset if it already exists, else create it
        self._ledfx.config['presets'][effect_id][preset_id] = {}
        self._ledfx.config['presets'][effect_id][preset_id]['name'] = preset_name
        self._ledfx.config['presets'][effect_id][preset_id]['config'] = device.active_effect.config

        save_config(
            config = self._ledfx.config, 
            config_dir = self._ledfx.config_dir)

        response = { 'status' : 'success', 'preset': {'id': preset_id, 'name' : preset_name, 'config': device.active_effect.config }}
        return web.Response(text=json.dumps(response), status=200)

    async def delete(self, device_id) -> web.Response:
        """clear effect of a device"""
        device = self._ledfx.devices.get(device_id)
        if device is None:
            response = { 'not found': 404 }
            return web.Response(text=json.dumps(response), status=404)

        # Clear the effect
        device.clear_effect()

        for device in self._ledfx.config['devices']:
            if (device['id'] == device_id):
                if 'effect' in device:
                    del device['effect']
                    break
        save_config(
            config = self._ledfx.config, 
            config_dir = self._ledfx.config_dir)

        response = { 'status' : 'success', 'effect' : {} }
        return web.Response(text=json.dumps(response), status=200)