def helloworldlang(app, *args, **kwargs):
    """[-l language]

    Print 'hello world' in the requested language.
    """
    lang = kwargs['language']
    code = kwargs['languages'].get(lang, None)

    if code is None:
        app.parser.error("Can't translate language '%s'" % lang)
        return 1

    msg = kwargs['translations'][code]

    print('%s!' % msg)

if __name__ == '__main__':
    from cli import App
    app = App(helloworldlang, config_file="examples/helloworld.conf")
    app.add_option("language",
        default='english',
        help="print message in Esperanto",
        action="store")
    app.run()

