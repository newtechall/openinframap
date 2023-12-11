# Generate the Tegola config and bake it into a container.
FROM python:3.9-slim AS build
WORKDIR /app
COPY . .
#RUN apt -y update
#RUN apt install -y iputils-ping
#RUN apt install -y vim
RUN pip install PyYAML toml
RUN python generate_tegola_config.py ./tegola.yml ./layers.yml > ./config.toml

FROM gospatial/tegola:v0.16.0
COPY --from=build /app/config.toml /etc/tegola/config.toml
#RUN cat /etc/gegola/config.toml


EXPOSE 80
ENTRYPOINT ["/opt/tegola"]
CMD ["serve", "--config", "/etc/tegola/config.toml"]
