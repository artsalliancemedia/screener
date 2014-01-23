"""
Message bus, adapted from cyrusbus by Bernardo Heynemann (https://github.com/heynemann/cyrusbus)
"""

class Bus(object):

    def __init__(self):
        self.reset()

    def subscribe(self, key, callback, force=False):
        if key not in self.subscriptions:
            self.subscriptions[key] = []

        if force or not self.has_subscription(key, callback):
            self.subscriptions[key].append(callback)

        return self # Return self so we can chain :)

    def unsubscribe(self, key, callback):
        if self.has_subscription(key, callback):
            self.subscriptions[key].remove(callback)

        return self

    def unsubscribe_all(self, key):
        if key in self.subscriptions:
            self.subscriptions[key] = []

        return self

    def has_subscription(self, key, callback):
        return key in self.subscriptions and callback in self.subscriptions[key]

    def has_any_subscriptions(self, key):
        return key in self.subscriptions and len(self.subscriptions[key]) > 0

    def publish(self, key, *args, **kwargs):
        for callback in self.subscriptions[key]:
            callback(self, *args, **kwargs)

        return self

    def reset(self):
        self.subscriptions = {}

        return self
