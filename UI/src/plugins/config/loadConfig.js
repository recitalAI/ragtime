import _axios from 'axios';

const openConfig = async configPath => {
  try {
    const config = await _axios.get(configPath);
    return config.data;
  } catch (error) {
    return null;
  }
};

const passConfigCheck = config => !(!config || !config.backend);

const loadConfig = async () => {
  console.log('Attempting to load config from /data/config.json');
  const config = await openConfig('/data/config.json');
  console.log('Loaded config:', config);
  if (passConfigCheck(config)) {
    console.log('Config passed check, returning:', config);
    return config;
  }
  console.log('Config failed check, returning false');
  return false;
};

export default loadConfig;
