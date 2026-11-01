#!/bin/bash
# Rebuilds the HTTP/3 toolchain into ~/.local (UNTESTED as a whole script: reconstructed from the build trees in ~/build,
# their config.log / objs files and shell history. The OpenSSL -> ~/.local step is NOT recorded anywhere and is an assumption.)
# Commits are the ones actually built. Takes a long time; needs: git build-essential cmake pkg-config autoconf libtool libpcre3-dev
set -e
P=$HOME/.local; B=$HOME/build; mkdir -p "$B"; cd "$B"
sudo apt install -y git build-essential cmake pkg-config autoconf libtool libpcre3-dev libssl-dev zlib1g-dev iproute2 wireshark zip
get() { [ -d "$1" ] || git clone "$2" "$1"; git -C "$1" checkout -q "$3"; }
get openssl https://github.com/openssl/openssl openssl-3.6.5
get nghttp3 https://github.com/ngtcp2/nghttp3 ac11a45    # v1.18.0-38-gac11a45
get ngtcp2  https://github.com/ngtcp2/ngtcp2  988eb237   # v1.25.0-176-g988eb237
get nghttp2 https://github.com/nghttp2/nghttp2 3baf956
get curl    https://github.com/curl/curl      705b02e
get nginx   https://github.com/nginx/nginx    797c039
git -C nghttp3 submodule update --init --recursive; git -C ngtcp2 submodule update --init --recursive
export PKG_CONFIG_PATH=$P/lib/pkgconfig LDFLAGS="-Wl,-rpath,$P/lib"
(cd openssl && ./Configure --prefix=$P --libdir=lib && make -j"$(nproc)" && make install_sw)   # ASSUMED install location
(cd nghttp3 && autoreconf -fi && ./configure --prefix=$P && make -j"$(nproc)" && make install)
(cd ngtcp2  && autoreconf -fi && ./configure --prefix=$P LDFLAGS="$LDFLAGS" --with-openssl && make -j"$(nproc)" && make install)
(cd nghttp2 && autoreconf -fi && ./configure --prefix=$P --enable-lib-only && make -j"$(nproc)" && make install)
(cd curl && autoreconf -fi && ./configure --prefix=$P --with-openssl=$P --with-ngtcp2=$P --with-nghttp3=$P --with-nghttp2=$P --without-libpsl LDFLAGS="$LDFLAGS" && make -j"$(nproc)" && make install)
# nginx builds its own OpenSSL from ~/build/openssl (--with-openssl)
(cd nginx && auto/configure --prefix=$P/nginx --with-http_ssl_module --with-http_v3_module --with-http_v2_module --with-openssl="$B/openssl" && make -j"$(nproc)" && make install)
# test content + self-signed certificate (IP SAN so curl --cacert works against 10.0.0.2)
mkdir -p ~/srv/certs ~/srv/content
head -c 1048576 /dev/urandom > ~/srv/content/1MB.bin; head -c 10485760 /dev/urandom > ~/srv/content/10MB.bin
openssl req -x509 -newkey rsa:2048 -nodes -days 365 -keyout ~/srv/certs/server.key -out ~/srv/certs/server.crt \
  -subj "/CN=10.0.0.2" -addext "subjectAltName=IP:10.0.0.2"
echo "done. Verify: ~/.local/bin/curl -V | head -2 ; ~/.local/nginx/sbin/nginx -V ; sudo modprobe sch_netem"
