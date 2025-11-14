import typer

app = typer.Typer(help="hello_redirect")

@app.command()
def hello():
    typer.echo(f"Hello from HelloRedirect")

