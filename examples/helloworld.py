def helloworld(app):
    print 'hello world.'

if __name__ == '__main__':
    from cli import App

    app = App(helloworld)
    app.run()

