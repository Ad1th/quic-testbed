# Linux image with the exact HTTP/3 toolchain pinned in scripts/build_toolchain.sh (same commits), for running the
# testbed on any Docker host. Run with --privileged (needs netns + tc netem). Ubuntu 22.04 / Python 3.10 as in the original.
FROM ubuntu:22.04
ENV DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends git ca-certificates build-essential cmake pkg-config autoconf \
    automake libtool libpcre3-dev zlib1g-dev iproute2 ethtool iputils-ping procps python3 python3-pip util-linux tcpdump \
    && rm -rf /var/lib/apt/lists/*
ENV P=/opt/h3 B=/build
WORKDIR /build
RUN git clone -q https://github.com/openssl/openssl && git -C openssl checkout -q openssl-3.6.5 \
 && git clone -q https://github.com/ngtcp2/nghttp3 && git -C nghttp3 checkout -q ac11a45 && git -C nghttp3 submodule update -q --init --recursive \
 && git clone -q https://github.com/ngtcp2/ngtcp2 && git -C ngtcp2 checkout -q 988eb237 && git -C ngtcp2 submodule update -q --init --recursive \
 && git clone -q https://github.com/nghttp2/nghttp2 && git -C nghttp2 checkout -q 3baf956 \
 && git clone -q https://github.com/curl/curl && git -C curl checkout -q 705b02e \
 && git clone -q https://github.com/nginx/nginx && git -C nginx checkout -q 797c039
ENV PKG_CONFIG_PATH=/opt/h3/lib/pkgconfig LDFLAGS="-Wl,-rpath,/opt/h3/lib"
RUN cd openssl && ./Configure --prefix=$P --libdir=lib && make -j"$(nproc)" >/dev/null && make install_sw >/dev/null
RUN cd nghttp3 && autoreconf -fi >/dev/null && ./configure -q --prefix=$P && make -j"$(nproc)" >/dev/null && make install >/dev/null
RUN cd ngtcp2 && autoreconf -fi >/dev/null && ./configure -q --prefix=$P --with-openssl && make -j"$(nproc)" >/dev/null && make install >/dev/null
RUN cd nghttp2 && autoreconf -fi >/dev/null && ./configure -q --prefix=$P --enable-lib-only && make -j"$(nproc)" >/dev/null && make install >/dev/null
RUN cd curl && autoreconf -fi >/dev/null && ./configure -q --prefix=$P --with-openssl=$P --with-ngtcp2=$P --with-nghttp3=$P --with-nghttp2=$P \
    --without-libpsl && make -j"$(nproc)" >/dev/null && make install >/dev/null
RUN cd nginx && auto/configure --prefix=$P/nginx --with-http_ssl_module --with-http_v3_module --with-http_v2_module --with-openssl=$B/openssl >/dev/null \
    && make -j"$(nproc)" >/dev/null && make install >/dev/null
RUN pip3 install -q pandas==2.3.3 numpy==2.2.6 scipy==1.15.3 matplotlib==3.10.9 aioquic==1.3.0
RUN mkdir -p /srv/certs /srv/content && head -c 1048576 /dev/urandom > /srv/content/1MB.bin && head -c 10485760 /dev/urandom > /srv/content/10MB.bin \
 && printf "[req]\ndistinguished_name=dn\n[dn]\n" > /tmp/o.cnf && LD_LIBRARY_PATH=/opt/h3/lib /opt/h3/bin/openssl req -config /tmp/o.cnf -x509 -newkey rsa:2048 -nodes -days 3650 -keyout /srv/certs/server.key -out /srv/certs/server.crt \
    -subj "/CN=10.0.0.2" -addext "subjectAltName=IP:10.0.0.2"
ENV PATH=/opt/h3/bin:$PATH
WORKDIR /work
