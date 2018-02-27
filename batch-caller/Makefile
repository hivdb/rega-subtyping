run:
	@docker-compose kill || true
	@docker-compose rm -f || true
	@rm keymap.txt 2>/dev/null || true
	@touch keymap.txt
	@docker-compose up -d

clean:
	@rm keymap.txt 2>/dev/null || true
	@./clean_jobs.sh
