"""
Adds support for first class features that can be added to the edX platform.
"""

from stevedore.extension import ExtensionManager

# The Stevedore extension point namespace for edx platform features.
FEATURE_NAMESPACE = 'openedx.feature'


class FeatureError(Exception):
    """
    Base Exception for when an error was found regarding features.
    """
    pass


class FeatureManager(object):
    """
    Manager for all of the edX features that have been made available.
    """
    @staticmethod
    def get_available_features():
        """
        Returns a dict of all the features that have been made available through the platform.
        """
        # Note: we're creating the extension manager lazily to ensure that the Python path
        # has been correctly set up. Trying to create this statically will fail, unfortunately.
        if not hasattr(FeatureManager, "_features"):
            features = {}
            extension_manager = ExtensionManager(namespace=FEATURE_NAMESPACE)
            for feature_name in extension_manager.names():
                feature = Feature(feature_name, extension_manager[feature_name].plugin)
                features[feature_name] = feature
            FeatureManager._features = features
        return FeatureManager._features

    @staticmethod
    def get_feature(name):
        """
        Returns the course feature with the given name.
        """
        features = FeatureManager.get_available_features()
        if name not in features:
            raise FeatureError("No such feature {name}".format(name=name))
        return features[name]


class Feature(object):
    """
    A feature on the edX platform that is usually provided as a Stevedore plug-in.
    """
    def __init__(self, name, plugin):
        self.name = name
        self.plugin = plugin

    def __getattr__(self, attr):
        return getattr(self.plugin, attr)
