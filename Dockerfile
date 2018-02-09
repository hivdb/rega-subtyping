FROM tomcat:7-jre8-alpine
ENV LANG=en_US.UTF-8
RUN ALPINE_GLIBC_BASE_URL="https://github.com/sgerrand/alpine-pkg-glibc/releases/download" && \
    ALPINE_GLIBC_PACKAGE_VERSION="2.23-r3" && \
    ALPINE_GLIBC_BASE_PACKAGE_FILENAME="glibc-$ALPINE_GLIBC_PACKAGE_VERSION.apk" && \
    ALPINE_GLIBC_BIN_PACKAGE_FILENAME="glibc-bin-$ALPINE_GLIBC_PACKAGE_VERSION.apk" && \
    ALPINE_GLIBC_I18N_PACKAGE_FILENAME="glibc-i18n-$ALPINE_GLIBC_PACKAGE_VERSION.apk" && \
    apk add --no-cache --virtual=.build-dependencies wget ca-certificates && \
    wget \
        "https://raw.githubusercontent.com/andyshinn/alpine-pkg-glibc/master/sgerrand.rsa.pub" \
        -O "/etc/apk/keys/sgerrand.rsa.pub" && \
    wget \
        "$ALPINE_GLIBC_BASE_URL/$ALPINE_GLIBC_PACKAGE_VERSION/$ALPINE_GLIBC_BASE_PACKAGE_FILENAME" \
        "$ALPINE_GLIBC_BASE_URL/$ALPINE_GLIBC_PACKAGE_VERSION/$ALPINE_GLIBC_BIN_PACKAGE_FILENAME" \
        "$ALPINE_GLIBC_BASE_URL/$ALPINE_GLIBC_PACKAGE_VERSION/$ALPINE_GLIBC_I18N_PACKAGE_FILENAME" && \
    apk add --no-cache \
        "$ALPINE_GLIBC_BASE_PACKAGE_FILENAME" \
        "$ALPINE_GLIBC_BIN_PACKAGE_FILENAME" \
        "$ALPINE_GLIBC_I18N_PACKAGE_FILENAME" && \
    \
    rm "/etc/apk/keys/sgerrand.rsa.pub" && \
    /usr/glibc-compat/bin/localedef --force --inputfile POSIX --charmap UTF-8 en_US.UTF-8 || true && \
    echo "export LANG=en_US.UTF-8" > /etc/profile.d/locale.sh && \
    \
    apk del glibc-i18n && \
    \
    rm "/root/.wget-hsts" && \
    apk del .build-dependencies && \
    rm \
        "$ALPINE_GLIBC_BASE_PACKAGE_FILENAME" \
        "$ALPINE_GLIBC_BIN_PACKAGE_FILENAME" \
        "$ALPINE_GLIBC_I18N_PACKAGE_FILENAME"
ARG tree_puzzle_version=5.3.rc16
RUN apk --no-cache add bash imagemagick inkscape && \
    apk --no-cache --virtual .install-deps add curl tar build-base && \
    cd /tmp && \
    curl http://www.tree-puzzle.de/tree-puzzle-${tree_puzzle_version}-linux.tar.gz \
         -o /tmp/tree-puzzle-${tree_puzzle_version}-linux.tar.gz && \
    tar xvf tree-puzzle-${tree_puzzle_version}-linux.tar.gz && \
    cd tree-puzzle-${tree_puzzle_version}-linux && \
    ./configure && make && make install && \
    apk --no-cache del .install-deps && \
    sed -i 's/v3\.4/v3.5/g' /etc/apk/repositories && \
    apk --no-cache add R-mathlib && \
    mkdir -p /opt/rega/jobs/NoV /opt/rega/jobs/HIV /opt/rega/jobs/HTLV
ADD config /opt/rega
ADD webapps/RegaSubtyping.war /usr/local/tomcat/webapps
ENV REGA_GENOTYPE_CONF_DIR /opt/rega/conf/
ENV CATALINA_OPTS "-Xmx12288m -Djava.security.egd=file:/dev/./urandom"
