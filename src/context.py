class Context:
    def __init__(self, env_vars={}, hex=None, distance=None, rgb=None):
        self.env_vars = env_vars
        self.hex = hex
        self.distance = distance
        self.rgb = rgb

    def __str__(self):
        return str(
            {
                "env_vars": str(self.env_vars),
                "hex": str(self.hex),
                "distance": str(self.distance),
                "rgb": str(self.rgb),
            }
        )

    def __unicode__(self):
        pass
