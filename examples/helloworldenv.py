def helloworldlang(app, *args, **kwargs):
    """[-l language]

    Print 'hello world' in the requested language.
    """
    if 'environment' in kwargs:
        app.log.debug("environment detected")
    msg = 'hello world'
    if kwargs['language'] == 'esperanto':
        msg = 'Saluton mondo'

    print('%s!' % msg)

if __name__ == '__main__':
    from cli import App

    env = {'HELLOWORLDLANG_ENVIRONMENT': 'foo'}
    app = App(helloworldlang, env=env)
    app.add_option("language",
        default='english',
        help="print message in Esperanto",
        action="store")
    app.run()

