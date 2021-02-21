import yaml
import jsonschema
import logging as log
from importlib import import_module


class ConfigParser:

    def __init__(self, config_file):
        self.schema = self._load_yaml('utils/settings_schema.yaml')
        self.config_file = config_file
        self.exchanges = {}
        self.strategies = {}
        self.config = {
            'exchanges': self.exchanges,
            'strategies': self.strategies
        }

    def init_config(self):
        config = self._load_yaml(self.config_file)
        obj = lambda t: getattr(import_module(t[0], t[1]))
        if self.validate_config(config):
            for exchange in config['exchanges']:
                self.exchanges[exchange['name']] = \
                    self._init_exchange(exchange)

            for strategy in config['strategies']:
                self.strategies[strategy['name']] = \
                    self._init_strategy(strategy)
        return self.config

    def _init_exchange(self, exch_config):
        exch = None
        try:
            klass = self._get_class(exch_config['type'])
            exch = klass(**exch_config['options'])
        except Exception:
            log.exception(f"Error creating exchange {exch_config['name']}")
        return exch

    def _init_strategy(self, strat_config):
        strat = None
        try:
            klass = self._get_class(strat_config['type'])
            exch = self.config['exchanges'][strat_config['exchange']]
            strat = klass(exch, **strat_config['options'])
        except Exception:
            log.exception(f"Error creating strategy {strat_config['name']}")
        return strat

    def _get_class(self, type):
        module, class_name = type.rsplit('.', 1)
        klass = None
        try:
            klass = getattr(import_module(module), class_name)
        except Exception:
            log.exception(f"Error creating object for {module}.{class_name}")
        return klass

    def _load_yaml(self, file):
        y = {}
        try:
            with open(file, 'r') as f:
                y = yaml.load(f, Loader=yaml.Loader)
        except Exception:
            log.exception("Error loading yaml")
        return y

    def validate_config(self, y):
        valid = True
        try:
            jsonschema.validate(y, self.schema)
        except jsonschema.ValidationError:
            valid = False
        return valid


if __name__ == '__main__':
    c = ConfigParser('../settings.yaml')
    c.init_config()