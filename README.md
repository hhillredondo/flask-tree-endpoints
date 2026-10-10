# Trees API

The backend for the family tree app. It stores the tree itself as a graph in
Amazon Neptune, so questions like "who are this person's grandchildren" are a
traversal rather than a pile of joins. Everything else lives in DynamoDB: who can
see which tree, and the editor lock that stops two people editing the same tree
at once.

A Flask app, deployed as a container on ECS Fargate. Requests arrive with a
Cognito JWT, which is verified on the way in, and every tree is scoped by a
partition key so one tree's data cannot be read through another's.

The frontend that talks to this lives in the `trees-amplify` repo.

## Running it locally

You need Python 3.11 or newer, and a Gremlin server on port 8182 if you want the
graph endpoints to do anything. The quickest way to get one is the TinkerPop
container:

```bash
docker run --rm -p 8182:8182 tinkerpop/gremlin-server
```

Then set up the app:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt -r requirements-dev.txt

cp .env.example .env
flask --debug run
```

The API comes up on http://localhost:5000, and `GET /` will tell you whether it
can reach Gremlin.

`.env.example` lists what you can set. The two worth knowing about are
`AMPLIFY_USER_POOL_ID` and `AMPLIFY_USER_POOL_CLIENT_ID`. Those come from a
deployed Cognito pool, and without them any request carrying a token is rejected,
so you will only be able to reach the health check.

There is no `FLASK_SECRET_KEY`. Nothing in the app is signed, so Flask runs
without one and refuses `session` and `flash` if code ever reaches for them.


## Tests

Run from the repository root, so imports like `config` resolve:

```bash
pytest
```
