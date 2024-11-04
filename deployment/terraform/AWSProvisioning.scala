import com.hashicorp.terraform._
import io.circe.syntax._
import io.circe.generic.auto._
import scala.sys.process._

object AWSProvisioning {

  case class VPCConfig(
    cidrBlock: String,
    instanceTenancy: String,
    enableDnsHostnames: Boolean
  )

  case class SubnetConfig(
    cidrBlock: String,
    vpcId: String,
    availabilityZone: String,
    mapPublicIpOnLaunch: Boolean
  )

  case class SecurityGroupConfig(
    vpcId: String,
    description: String,
    ingress: List[IngressRule],
    egress: List[EgressRule]
  )

  case class IngressRule(
    protocol: String,
    fromPort: Int,
    toPort: Int,
    cidrBlocks: List[String]
  )

  case class EgressRule(
    protocol: String,
    fromPort: Int,
    toPort: Int,
    cidrBlocks: List[String]
  )

  case class EC2Config(
    ami: String,
    instanceType: String,
    keyName: String,
    subnetId: String,
    securityGroupIds: List[String]
  )

  def createVPC(config: VPCConfig): String = {
    val vpc = s"""
      resource "aws_vpc" "main" {
        cidr_block = "${config.cidrBlock}"
        instance_tenancy = "${config.instanceTenancy}"
        enable_dns_hostnames = ${config.enableDnsHostnames}
      }
    """
    writeFile("vpc.tf", vpc)
  }

  def createSubnet(config: SubnetConfig): String = {
    val subnet = s"""
      resource "aws_subnet" "main" {
        vpc_id = "${config.vpcId}"
        cidr_block = "${config.cidrBlock}"
        availability_zone = "${config.availabilityZone}"
        map_public_ip_on_launch = ${config.mapPublicIpOnLaunch}
      }
    """
    writeFile("subnet.tf", subnet)
  }

  def createSecurityGroup(config: SecurityGroupConfig): String = {
    val ingressRules = config.ingress.map { rule =>
      s"""
        ingress {
          protocol = "${rule.protocol}"
          from_port = ${rule.fromPort}
          to_port = ${rule.toPort}
          cidr_blocks = [${rule.cidrBlocks.map(b => s""""$b"""").mkString(", ")}]
        }
      """
    }.mkString("\n")

    val egressRules = config.egress.map { rule =>
      s"""
        egress {
          protocol = "${rule.protocol}"
          from_port = ${rule.fromPort}
          to_port = ${rule.toPort}
          cidr_blocks = [${rule.cidrBlocks.map(b => s""""$b"""").mkString(", ")}]
        }
      """
    }.mkString("\n")

    val securityGroup = s"""
      resource "aws_security_group" "main" {
        vpc_id = "${config.vpcId}"
        description = "${config.description}"

        $ingressRules

        $egressRules
      }
    """
    writeFile("security_group.tf", securityGroup)
  }

  def createEC2Instance(config: EC2Config): String = {
    val ec2Instance = s"""
      resource "aws_instance" "main" {
        ami = "${config.ami}"
        instance_type = "${config.instanceType}"
        key_name = "${config.keyName}"
        subnet_id = "${config.subnetId}"
        security_group_ids = [${config.securityGroupIds.map(id => s""""$id"""").mkString(", ")}]
      }
    """
    writeFile("ec2_instance.tf", ec2Instance)
  }

  def applyTerraform(): Unit = {
    val init = "terraform init".!!
    val apply = "terraform apply -auto-approve".!!
    println(s"Terraform init: $init")
    println(s"Terraform apply: $apply")
  }

  def writeFile(fileName: String, content: String): Unit = {
    import java.io._
    val pw = new PrintWriter(new File(fileName))
    pw.write(content)
    pw.close()
  }

  def main(args: Array[String]): Unit = {
    val vpcConfig = VPCConfig(
      cidrBlock = "10.0.0.0/16",
      instanceTenancy = "default",
      enableDnsHostnames = true
    )

    val subnetConfig = SubnetConfig(
      cidrBlock = "10.0.1.0/24",
      vpcId = "aws_vpc.main.id",
      availabilityZone = "us-west-2a",
      mapPublicIpOnLaunch = true
    )

    val securityGroupConfig = SecurityGroupConfig(
      vpcId = "aws_vpc.main.id",
      description = "Allow SSH and HTTP",
      ingress = List(
        IngressRule(
          protocol = "tcp",
          fromPort = 22,
          toPort = 22,
          cidrBlocks = List("0.0.0.0/0")
        ),
        IngressRule(
          protocol = "tcp",
          fromPort = 80,
          toPort = 80,
          cidrBlocks = List("0.0.0.0/0")
        )
      ),
      egress = List(
        EgressRule(
          protocol = "-1",
          fromPort = 0,
          toPort = 0,
          cidrBlocks = List("0.0.0.0/0")
        )
      )
    )

    val ec2Config = EC2Config(
      ami = "ami-0c55b159cbfafe1f0",
      instanceType = "t2.micro",
      keyName = "key",
      subnetId = "aws_subnet.main.id",
      securityGroupIds = List("aws_security_group.main.id")
    )

    // Create resources
    createVPC(vpcConfig)
    createSubnet(subnetConfig)
    createSecurityGroup(securityGroupConfig)
    createEC2Instance(ec2Config)

    // Apply Terraform
    applyTerraform()
  }
}