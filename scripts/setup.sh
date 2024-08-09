#!/bin/bash

# setup homebrew
echo "Installing homebrew..."
[ ! -f "`which brew`" ] && /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)" && brew update || echo "homebrew already present."


# Add awscli if not present
echo "Installing awscli..."
if brew ls --versions awscli > /dev/null; then
    # The package is installed
    echo "awscli already present."
else
    # The package is not installed
    brew install awscli
fi

# configure aws profile with access key and secret from AWS
# if not already configured
echo "Configuring AWS Profile..."
[[ $(aws configure --profile labramp-dev list) && $? -eq 0 ]] && echo "AWS Profile already present." || aws configure --profile labramp-dev

# install docker desktop if not present
echo "Installing docker..."
[ ! -f "`which docker`" ] && brew install --cask docker || echo "docker already present"

echo "Setup Successful."

exit 0
