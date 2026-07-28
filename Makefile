.PHONY: dev test demo gen-types down logs

dev:
	docker compose -f infra/docker-compose.yml up --build

down:
	docker compose -f infra/docker-compose.yml down

logs:
	docker compose -f infra/docker-compose.yml logs -f

test:
	@echo "Backend/frontend test suites are added starting Day 2+"

demo:
	@echo "Demo scenario script is added Day 7"

gen-types:
	@echo "OpenAPI -> TS type generation is added once backend routes exist"
