up: 
	docker compose -f compose.yaml --profile routers --profile endpoints up -d

down:
	docker compose -f compose.yaml --profile routers --profile endpoints down -t 1

clean:
	-@echo "Cleaning..."
	-@rm -rf __pycache__

veryclean: clean down
	-@echo "Scrubbing images..."
	-@docker image rm pycimage
	-@docker image prune -fa
