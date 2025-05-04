# main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }
}

provider "aws" {
  region = "us-east-1"
}

# Create VPC
resource "aws_vpc" "url_shortener_vpc" {
  cidr_block           = "10.0.0.0/16"
  enable_dns_support   = true
  enable_dns_hostnames = true
  tags = {
    Name = "url-shortener-vpc"
  }
}

# Create Internet Gateway
resource "aws_internet_gateway" "gw" {
  vpc_id = aws_vpc.url_shortener_vpc.id
  tags = {
    Name = "url-shortener-igw"
  }
}

# Create Public Subnet
resource "aws_subnet" "public_subnet" {
  vpc_id                  = aws_vpc.url_shortener_vpc.id
  cidr_block              = "10.0.1.0/24"
  availability_zone       = "us-east-1a"
  map_public_ip_on_launch = true
  tags = {
    Name = "url-shortener-public-subnet"
  }
}

# Create Route Table
resource "aws_route_table" "public_rt" {
  vpc_id = aws_vpc.url_shortener_vpc.id
  route {
    cidr_block = "0.0.0.0/0"
    gateway_id = aws_internet_gateway.gw.id
  }
  tags = {
    Name = "url-shortener-rt"
  }
}

# Associate Route Table with Subnet
resource "aws_route_table_association" "public_rta" {
  subnet_id      = aws_subnet.public_subnet.id
  route_table_id = aws_route_table.public_rt.id
}

# Create Security Group
resource "aws_security_group" "url_shortener_sg" {
  name        = "url-shortener-sg"
  description = "Allow HTTP and SSH traffic"
  vpc_id      = aws_vpc.url_shortener_vpc.id

  ingress {
    description = "HTTP"
    from_port   = 5000
    to_port     = 5000
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    description = "SSH"
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "allow_web"
  }
}

# Create EC2 Instance
resource "aws_instance" "url_shortener" {
  ami                    = "ami-0c55b159cbfafe1f0" # Ubuntu 22.04 LTS
  instance_type          = "t2.micro"
  key_name               = "your-keypair" # Replace with your key pair name
  subnet_id              = aws_subnet.public_subnet.id
  vpc_security_group_ids = [aws_security_group.url_shortener_sg.id]
  user_data              = <<-EOF
                          #!/bin/bash
                          sudo apt-get update -y
                          sudo apt-get install docker.io -y
                          sudo systemctl start docker
                          sudo systemctl enable docker
                          sudo docker run -d -p 5000:5000 --name url-shortener your-dockerhub/url-shortener
                          EOF

  tags = {
    Name = "url-shortener-instance"
  }
}

# Output the Public IP
output "instance_public_ip" {
  value = aws_instance.url_shortener.public_ip
  description = "Public IP of the EC2 instance"
}