docker buildx build \
    --platform linux/amd64,  # Intel/AMD 64位
           linux/arm64,     # ARM 64位 (如苹果M1/M2、树莓派4)
           linux/arm/v7,    # ARM 32位 (如树莓派3/Zero 2W)
           linux/ppc64le    # IBM PowerPC 64位小端模式
    -t chatspeedbot .