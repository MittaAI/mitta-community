# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set non-interactive installation (to avoid prompts during build)
ENV DEBIAN_FRONTEND=noninteractive

# Create a new sources.list file with the specified mirror
RUN echo "deb https://debian.csail.mit.edu/debian/ bullseye main" > /etc/apt/sources.list \
    && echo "deb https://debian.csail.mit.edu/debian/ bullseye-updates main" >> /etc/apt/sources.list \
    && echo "deb http://security.debian.org/debian-security bullseye-security main" >> /etc/apt/sources.list

# Basic build tools and libraries
RUN apt-get update && apt-get install -y \
    autoconf \
    automake \
    build-essential \
    cmake \
    git-core \
    pkg-config \
    texinfo \
    wget \
    nasm \
    yasm \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Libraries for video/audio processing
RUN apt-get update && apt-get install -y \
    libass-dev \
    libfreetype6-dev \
    libgnutls28-dev \
    libmp3lame-dev \
    libopus-dev \
    libtool \
    libvorbis-dev \
    libvpx-dev \
    libx264-dev \
    libx265-dev \
    libdav1d-dev \
    libsvtav1-dev \
    libnuma-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set up environment variables
ENV PATH="/root/bin:$PATH" \
    PKG_CONFIG_PATH="/root/ffmpeg_build/lib/pkgconfig"

# Create a directory for FFmpeg sources
WORKDIR /root/ffmpeg_sources

# Clone, build, and install Fraunhofer FDK AAC Codec Library
RUN mkdir -p /root/ffmpeg_sources && cd /root/ffmpeg_sources \
    && git -C fdk-aac pull 2> /dev/null || git clone --depth 1 https://github.com/mstorsjo/fdk-aac \
    && cd fdk-aac \
    && autoreconf -fiv \
    && ./configure --prefix="/root/ffmpeg_build" --disable-shared \
    && make -j4 \
    && make install

# Clone, build, and install AOM (AV1 codec)
RUN git -C aom pull 2> /dev/null || git clone --depth 1 https://aomedia.googlesource.com/aom \
    && mkdir -p aom_build \
    && cd aom_build \
    && cmake -G "Unix Makefiles" \
       -DCMAKE_INSTALL_PREFIX="/root/ffmpeg_build" \
       -DENABLE_TESTS=OFF \
       -DENABLE_NASM=on ../aom \
    && make -j4 \
    && make install

# Get to gnutls
RUN apt-get -y update && apt-get -y install libunistring-dev

# Clone, build, and install SVT-AV1
RUN git -C SVT-AV1 pull 2> /dev/null || git clone https://gitlab.com/AOMediaCodec/SVT-AV1.git \
    && mkdir -p SVT-AV1/build \
    && cd SVT-AV1/build \
    && cmake -G "Unix Makefiles" \
       -DCMAKE_INSTALL_PREFIX="/root/ffmpeg_build" \
       -DCMAKE_BUILD_TYPE=Release \
       -DBUILD_DEC=OFF \
       -DBUILD_SHARED_LIBS=OFF .. \
    && make -j4 \
    && make install

# Download and extract the FFmpeg source
# Download and extract FFmpeg version 6.1.1
RUN wget -O ffmpeg-6.1.1.tar.xz https://ffmpeg.org/releases/ffmpeg-6.1.1.tar.xz \
    && tar xJf ffmpeg-6.1.1.tar.xz \
    && cd ffmpeg-6.1.1 \
    && ./configure \
      --prefix="/root/ffmpeg_build" \
      --pkg-config-flags="--static" \
      --extra-cflags="-I/root/ffmpeg_build/include" \
      --extra-ldflags="-L/root/ffmpeg_build/lib" \
      --extra-libs="-lpthread -lm" \
      --ld="g++" \
      --bindir="/root/bin" \
      --enable-gpl \
      --enable-gnutls \
      --enable-libaom \
      --enable-libass \
      --enable-libfdk-aac \
      --enable-libfreetype \
      --enable-libmp3lame \
      --enable-libopus \
      --enable-libsvtav1 \
      --enable-libdav1d \
      --enable-libvorbis \
      --enable-libvpx \
      --enable-libx264 \
      --enable-libx265 \
      --enable-nonfree \
    && make -j4 \
    && make install \
    && hash -r

# Create a directory for app
WORKDIR /app

# Install Quart and Hypercorn
RUN pip install --no-cache-dir quart httpx werkzeug hypercorn

# Copy the current directory contents into the container at /app
COPY . /app

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Define environment variable
ENV QUART_APP=app:app
ENV QUART_ENV=production

# Run app.py using Hypercorn
CMD ["hypercorn", "--bind", "0.0.0.0:5000", "app:app"]
