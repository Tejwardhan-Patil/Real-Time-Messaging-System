package main

import (
	"fmt"
	"log"

	"github.com/aws/aws-sdk-go/aws"
	"github.com/aws/aws-sdk-go/aws/session"
	"github.com/aws/aws-sdk-go/service/autoscaling"
	"github.com/aws/aws-sdk-go/service/ec2"
)

// Initializes AWS Session
func initAWSSession() *session.Session {
	sess, err := session.NewSession(&aws.Config{
		Region: aws.String("us-west-2"),
	})
	if err != nil {
		log.Fatalf("Failed to create AWS session: %v", err)
	}
	return sess
}

// Creates Launch Configuration
func createLaunchConfiguration(svc *autoscaling.AutoScaling) {
	launchConfigName := "Exporterlaunch-config"

	_, err := svc.CreateLaunchConfiguration(&autoscaling.CreateLaunchConfigurationInput{
		LaunchConfigurationName: aws.String(launchConfigName),
		ImageId:                 aws.String("ami-12345678"),
		InstanceType:            aws.String("t2.micro"),
		KeyName:                 aws.String("Exporterkey-pair"),
		SecurityGroups:          []*string{aws.String("sg-012345678")},
	})
	if err != nil {
		log.Fatalf("Failed to create launch configuration: %v", err)
	}

	fmt.Printf("Launch Configuration %s created successfully\n", launchConfigName)
}

// Creates Auto Scaling Group
func createAutoScalingGroup(svc *autoscaling.AutoScaling) {
	autoScalingGroupName := "Exporterauto-scaling-group"

	_, err := svc.CreateAutoScalingGroup(&autoscaling.CreateAutoScalingGroupInput{
		AutoScalingGroupName:    aws.String(autoScalingGroupName),
		LaunchConfigurationName: aws.String("Exporterlaunch-config"),
		MinSize:                 aws.Int64(1),
		MaxSize:                 aws.Int64(5),
		DesiredCapacity:         aws.Int64(2),
		VPCZoneIdentifier:       aws.String("subnet-012345678"),
	})
	if err != nil {
		log.Fatalf("Failed to create Auto Scaling Group: %v", err)
	}

	fmt.Printf("Auto Scaling Group %s created successfully\n", autoScalingGroupName)
}

// Attaches Load Balancer to Auto Scaling Group
func attachLoadBalancer(svc *autoscaling.AutoScaling) {
	autoScalingGroupName := "Exporterauto-scaling-group"
	loadBalancerName := "Exporterload-balancer"

	_, err := svc.AttachLoadBalancers(&autoscaling.AttachLoadBalancersInput{
		AutoScalingGroupName: aws.String(autoScalingGroupName),
		LoadBalancerNames:    []*string{aws.String(loadBalancerName)},
	})
	if err != nil {
		log.Fatalf("Failed to attach Load Balancer to Auto Scaling Group: %v", err)
	}

	fmt.Printf("Load Balancer %s attached to Auto Scaling Group %s\n", loadBalancerName, autoScalingGroupName)
}

// Attaches Target Group to Auto Scaling Group
func attachTargetGroup(svc *autoscaling.AutoScaling) {
	autoScalingGroupName := "Exporterauto-scaling-group"
	targetGroupARN := "arn:aws:elasticloadbalancing:region:account-id:targetgroup/Exportertarget-group/123456789"

	_, err := svc.AttachLoadBalancerTargetGroups(&autoscaling.AttachLoadBalancerTargetGroupsInput{
		AutoScalingGroupName: aws.String(autoScalingGroupName),
		TargetGroupARNs:      []*string{aws.String(targetGroupARN)},
	})
	if err != nil {
		log.Fatalf("Failed to attach Target Group to Auto Scaling Group: %v", err)
	}

	fmt.Printf("Target Group %s attached to Auto Scaling Group %s\n", targetGroupARN, autoScalingGroupName)
}

// Configures Auto Scaling Policies
func configureScalingPolicies(svc *autoscaling.AutoScaling) {
	autoScalingGroupName := "Exporterauto-scaling-group"

	// Scale up policy
	scaleUpPolicyOutput, err := svc.PutScalingPolicy(&autoscaling.PutScalingPolicyInput{
		AutoScalingGroupName: aws.String(autoScalingGroupName),
		PolicyName:           aws.String("scale-up-policy"),
		AdjustmentType:       aws.String("ChangeInCapacity"),
		ScalingAdjustment:    aws.Int64(1),
		Cooldown:             aws.Int64(300),
	})
	if err != nil {
		log.Fatalf("Failed to create scale-up policy: %v", err)
	}

	fmt.Printf("Scale-up Policy created: %s\n", *scaleUpPolicyOutput.PolicyARN)

	// Scale down policy
	scaleDownPolicyOutput, err := svc.PutScalingPolicy(&autoscaling.PutScalingPolicyInput{
		AutoScalingGroupName: aws.String(autoScalingGroupName),
		PolicyName:           aws.String("scale-down-policy"),
		AdjustmentType:       aws.String("ChangeInCapacity"),
		ScalingAdjustment:    aws.Int64(-1),
		Cooldown:             aws.Int64(300),
	})
	if err != nil {
		log.Fatalf("Failed to create scale-down policy: %v", err)
	}

	fmt.Printf("Scale-down Policy created: %s\n", *scaleDownPolicyOutput.PolicyARN)
}

// Configures Auto Scaling Group's scheduled actions
func configureScheduledActions(svc *autoscaling.AutoScaling) {
	autoScalingGroupName := "Exporterauto-scaling-group"

	_, err := svc.PutScheduledUpdateGroupAction(&autoscaling.PutScheduledUpdateGroupActionInput{
		AutoScalingGroupName: aws.String(autoScalingGroupName),
		ScheduledActionName:  aws.String("scale-up-morning"),
		Recurrence:           aws.String("30 8 * * *"),
		MinSize:              aws.Int64(3),
		MaxSize:              aws.Int64(5),
		DesiredCapacity:      aws.Int64(3),
	})
	if err != nil {
		log.Fatalf("Failed to configure scheduled action: %v", err)
	}

	fmt.Printf("Scheduled action scale-up-morning created\n")
}

// Describes Auto Scaling Group
func describeAutoScalingGroup(svc *autoscaling.AutoScaling) {
	autoScalingGroupName := "Exporterauto-scaling-group"

	result, err := svc.DescribeAutoScalingGroups(&autoscaling.DescribeAutoScalingGroupsInput{
		AutoScalingGroupNames: []*string{aws.String(autoScalingGroupName)},
	})
	if err != nil {
		log.Fatalf("Failed to describe Auto Scaling Group: %v", err)
	}

	for _, group := range result.AutoScalingGroups {
		fmt.Printf("Auto Scaling Group: %s\n", *group.AutoScalingGroupName)
		fmt.Printf("Desired Capacity: %d\n", *group.DesiredCapacity)
		fmt.Printf("Min Size: %d\n", *group.MinSize)
		fmt.Printf("Max Size: %d\n", *group.MaxSize)
		fmt.Printf("Instance IDs: %v\n", group.Instances)
	}
}

// Terminates an instance in Auto Scaling Group
func terminateInstanceInAutoScalingGroup(svc *autoscaling.AutoScaling, ec2Svc *ec2.EC2) {
	autoScalingGroupName := "Exporterauto-scaling-group"

	result, err := svc.DescribeAutoScalingGroups(&autoscaling.DescribeAutoScalingGroupsInput{
		AutoScalingGroupNames: []*string{aws.String(autoScalingGroupName)},
	})
	if err != nil {
		log.Fatalf("Failed to describe Auto Scaling Group: %v", err)
	}

	if len(result.AutoScalingGroups) > 0 && len(result.AutoScalingGroups[0].Instances) > 0 {
		instanceID := result.AutoScalingGroups[0].Instances[0].InstanceId

		_, err = ec2Svc.TerminateInstances(&ec2.TerminateInstancesInput{
			InstanceIds: []*string{instanceID},
		})
		if err != nil {
			log.Fatalf("Failed to terminate instance %s: %v", *instanceID, err)
		}

		fmt.Printf("Terminated instance %s\n", *instanceID)
	} else {
		fmt.Println("No instances found to terminate")
	}
}

func main() {
	sess := initAWSSession()

	autoScalingSvc := autoscaling.New(sess)
	ec2Svc := ec2.New(sess)

	// Step-by-step operations
	createLaunchConfiguration(autoScalingSvc)
	createAutoScalingGroup(autoScalingSvc)
	attachLoadBalancer(autoScalingSvc)
	attachTargetGroup(autoScalingSvc)
	configureScalingPolicies(autoScalingSvc)
	configureScheduledActions(autoScalingSvc)
	describeAutoScalingGroup(autoScalingSvc)
	terminateInstanceInAutoScalingGroup(autoScalingSvc, ec2Svc)
}
