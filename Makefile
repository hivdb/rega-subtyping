build:
	docker build -t hivdb/rega-subtyping .

save:
	docker save -o rega-subtyping.image hivdb/rega-subtyping

start:
	@mkdir -p jobs/HIV jobs/NoV jobs/HTLV
	docker run --rm --publish 127.0.0.1:8081:8080 --volume `pwd`/jobs:/opt/rega/jobs --name rega-subtyping-instance hivdb/rega-subtyping

shell:
	docker run --rm -it --entrypoint /bin/bash hivdb/rega-subtyping

inspect:
	docker exec -it rega-subtyping-instance /bin/bash

.PHONY: build start shell inspect
